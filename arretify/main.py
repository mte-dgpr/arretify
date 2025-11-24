#
# Copyright (c) 2025 Direction générale de la prévention des risques (DGPR).
#
# This file is part of Arrêtify.
# See https://github.com/mte-dgpr/arretify for further info.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import logging
import sys
import traceback
from dataclasses import dataclass
from dataclasses import replace as dataclass_replace
from datetime import datetime
from optparse import OptionParser
from pathlib import Path

from dotenv import load_dotenv

from .errors import ArretifyError, DependencyError, ErrorCodes, SettingsError
from .law_data.apis.eurlex import initialize_eurlex_client
from .law_data.apis.legifrance import initialize_legifrance_client
from .law_data.apis.mistral import initialize_mistral_client
from .pipeline import (
    PipelineStep,
    load_ocr_file,
    load_ocr_pages,
    load_pdf_file,
    run_pipeline,
    save_html_file,
)
from .settings import OCR_FILE_EXTENSION, Settings
from .step_consolidation import step_consolidation
from .step_markdown_cleaning import step_markdown_cleaning
from .step_ocr import step_ocr
from .step_references_detection import step_references_detection
from .step_references_resolution import (
    step_eurlex_references_resolution,
    step_legifrance_references_resolution,
)
from .step_segmentation import step_segmentation
from .types import DocumentContext, SessionContext
from .utils.files import is_ocr_pages_dir, is_ocr_path, is_pdf_path

_LOGGER = logging.getLogger("arretify")


def main_cli() -> None:
    main(sys.argv[1:])


def main(args: list[str]) -> None:
    parser = OptionParser()
    parser.add_option(
        "-i",
        "--input",
        help="Input folder or single file path.",
    )
    parser.add_option(
        "-o",
        "--output",
    )
    parser.add_option(
        "-v",
        "--verbose",
        action="store_true",
        default=False,
        help="Enable verbose logging.",
    )
    parser.add_option(
        "--log-file",
        help="Path to the log file.",
    )
    parser.add_option(
        "-r",
        "--recursive",
        action="store_true",
        default=False,
        help="Search for input files in all sub-directories.",
    )

    (options, args) = parser.parse_args(args=args)

    # Check required options
    if not options.input:
        parser.error("Option -i/--input is required")
    if not options.output:
        parser.error("Option -o/--output is required")

    # ---------------- Initialization ---------------- #
    # Initialize environment variables before anything else
    load_dotenv()

    settings = Settings.from_env()
    session_context = SessionContext(
        settings=settings,
    )

    # Then initialize logging, so we don't miss any messages
    _initialize_root_logger(
        settings, _LOGGER, options.verbose, options.log_file and Path(options.log_file)
    )

    root_input_path = Path(options.input)
    root_output_path = Path(options.output)
    is_recursive = options.recursive
    features = _Features()
    was_ocr_disabled_warning_given = False

    if not root_input_path.exists():
        _LOGGER.error(f"Input path does not exist: {root_input_path}")
        sys.exit(1)

    # Initialize Mistral client
    try:
        session_context = initialize_mistral_client(session_context)
    except (SettingsError, DependencyError):
        pass
    else:
        _LOGGER.info("Mistral OCR is active")
        features = dataclass_replace(features, ocr=True)

    # Initialize Legifrance client
    try:
        session_context = initialize_legifrance_client(session_context)
    except SettingsError:
        _LOGGER.info(
            "Legifrance credentials not provided, skipping Legifrance references resolution"
        )
    except ArretifyError as error:
        if error.code is ErrorCodes.law_data_api_error:
            _LOGGER.warning("failed to initialize Legifrance client")
    else:
        _LOGGER.info("Legifrance references resolution is active")
        features = dataclass_replace(features, legifrance=True)

    # Initialize Eurlex client
    try:
        session_context = initialize_eurlex_client(session_context)
    except SettingsError:
        _LOGGER.info("Eurlex credentials not provided, skipping Eurlex references resolution")
    else:
        _LOGGER.info("Eurlex references resolution is active")
        features = dataclass_replace(features, eurlex=True)

    # ---------------- Processing ---------------- #
    if root_input_path.is_dir() and is_recursive:
        if root_output_path.exists() and not root_output_path.is_dir():
            _LOGGER.error(f"Expected output to be a directory, got {root_output_path}")
            sys.exit(1)

        all_input_file_paths = _walk_input_dir(root_input_path)
        for i, input_path in enumerate(all_input_file_paths):
            relative_input_path = input_path.relative_to(root_input_path)
            output_dir = root_output_path / relative_input_path.parent
            output_dir.mkdir(parents=True, exist_ok=True)
            output_stem = input_path.name if input_path.is_dir() else input_path.stem
            output_path = output_dir / f"{output_stem}.html"
            ocr_pages_dir: Path | None = None

            input_path_display = relative_input_path
            output_path_display = output_path.relative_to(root_output_path)

            _LOGGER.info(
                f"\n\n[{i + 1}/{len(all_input_file_paths)}] processing {input_path_display} ..."
            )

            if is_pdf_path(input_path):
                if features.ocr is False:
                    if not was_ocr_disabled_warning_given:
                        _ocr_disabled_warning()
                        was_ocr_disabled_warning_given = True

                    _LOGGER.warning(
                        f"Skipping {input_path} because it is a PDF and OCR support is not enabled."
                    )
                    continue

                ocr_pages_dir = (
                    session_context.settings.tmp_dir
                    / "ocr"
                    / relative_input_path.parent
                    / output_stem
                )
                ocr_pages_dir.mkdir(parents=True, exist_ok=True)
                _LOGGER.info(f"OCR pages will be stored at {ocr_pages_dir}")

            try:
                _process_arrete(
                    session_context,
                    input_path,
                    output_path,
                    features,
                    ocr_pages_dir=ocr_pages_dir,
                )
            except Exception:
                _LOGGER.error(f"❌ FAILED : {input_path_display} ...")
                error_traceback = traceback.format_exc()
                _LOGGER.error(f"Traceback:\n{error_traceback}")
            else:
                _LOGGER.info(f"✅ DONE : {output_path_display} ...")

    else:
        if is_pdf_path(root_input_path) and features.ocr is False:
            _ocr_disabled_warning()
            _LOGGER.error(
                f"Failed to process {root_input_path} because it is a PDF "
                "and OCR support is not enabled."
            )
            sys.exit(1)

        _process_arrete(
            session_context,
            root_input_path,
            root_output_path,
            features,
        )


def _walk_input_dir(
    root_dir_path: Path,
) -> list[Path]:
    paths: list[Path] = []
    for dir_path, sub_dir_names, file_names in root_dir_path.walk():
        # If we have entered a subdirectory that contains OCR pages,
        # we do not want to process it again.
        if dir_path not in paths:
            paths.extend(
                [
                    dir_path / file_name
                    for file_name in file_names
                    if is_ocr_path(dir_path / file_name)
                ]
            )

        paths.extend(
            [dir_path / file_name for file_name in file_names if is_pdf_path(dir_path / file_name)]
        )

        paths.extend(
            [
                dir_path / sub_dir_name
                for sub_dir_name in sub_dir_names
                if is_ocr_pages_dir(dir_path / sub_dir_name)
            ]
        )

    # Sort the files to ensure consistent order (useful for snapshot testing)
    return sorted(paths, key=lambda p: str(p))


@dataclass(frozen=True)
class _Features:
    ocr: bool = False
    legifrance: bool = False
    eurlex: bool = False


def _process_arrete(
    session_context: SessionContext,
    input_path: Path,
    output_path: Path,
    features: _Features,
    ocr_pages_dir: Path | None = None,
) -> None:
    """
    Process a single arrêté. `input_path` can be :
    - Path of a single .md file
    - Path of a single .pdf file
    - Path to a folder containing markdown pages named like so : 1.md, 2.md, ...
    """
    pipeline_steps: list[PipelineStep] = [
        step_markdown_cleaning,
        step_segmentation,
        step_references_detection,
    ]

    if features.legifrance:
        pipeline_steps.append(step_legifrance_references_resolution)
    if features.eurlex:
        pipeline_steps.append(step_eurlex_references_resolution)
    pipeline_steps.append(step_consolidation)

    document_context: DocumentContext
    if is_pdf_path(input_path):
        if not features.ocr:
            raise RuntimeError("OCR is disabled.")

        if ocr_pages_dir is not None:

            def step_ocr_with_settings(document_context: DocumentContext) -> DocumentContext:
                return step_ocr(
                    document_context,
                    ocr_pages_dir=ocr_pages_dir,
                )

            pipeline_steps.insert(0, step_ocr_with_settings)
        else:
            pipeline_steps.insert(0, step_ocr)

        document_context = load_pdf_file(
            session_context,
            input_path,
        )
    elif is_ocr_path(input_path):
        document_context = load_ocr_file(
            session_context,
            input_path,
        )
    elif is_ocr_pages_dir(input_path):
        document_context = load_ocr_pages(
            session_context,
            input_path,
        )
    else:
        if input_path.is_file():
            raise ValueError(
                f'Unsupported file "{input_path}", expected .pdf or .{OCR_FILE_EXTENSION} file.'
            )
        else:
            raise ValueError(
                f'Unsupported directory "{input_path}", '
                f"use -r or --recursive to process all files in subdirectories."
            )

    save_html_file(
        output_path,
        run_pipeline(
            document_context,
            pipeline_steps,
        ),
    )


def _ocr_disabled_warning() -> None:
    _LOGGER.warning(
        "To enable OCR processing for pdf input : "
        "\n- provide MistralAI credentials"
        "\n- install arretify with : pip install arretify[mistral]"
    )


class _MainLoggingFormatter(logging.Formatter):
    def __init__(self):
        super().__init__()
        self.simple_formatter = logging.Formatter("%(message)s")
        self.warning_formatter = logging.Formatter("%(levelname)s - %(message)s")

    def format(self, record: logging.LogRecord) -> str:
        if record.levelno >= logging.WARNING:
            return self.warning_formatter.format(record)
        else:
            return self.simple_formatter.format(record)


def _initialize_root_logger(
    settings: Settings, logger: logging.Logger, verbose: bool, log_file: Path | None
) -> None:
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(_MainLoggingFormatter())
    handlers: list[logging.Handler] = [stream_handler]

    if log_file is not None or settings.env == "development":
        if settings.env == "development":
            # Configure root logger
            log_dir = settings.tmp_dir / "log"
            log_dir.mkdir(exist_ok=True)
            log_file = log_dir / f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"

        assert log_file
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))

    logging.basicConfig(
        level=logging.INFO,
        handlers=handlers,
    )

    if log_file is not None:
        _LOGGER.info(f"Logging to file: {log_file}")

    # Set level globally based on verbosity flag
    if verbose:
        logger.setLevel(logging.DEBUG)


if __name__ == "__main__":
    main_cli()
