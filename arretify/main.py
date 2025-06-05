import sys
from typing import Tuple, List
from pathlib import Path
from optparse import OptionParser
import traceback
import logging
from datetime import datetime
from dataclasses import dataclass, replace as dataclass_replace

from dotenv import load_dotenv

from .types import SessionContext, ParsingContext
from .settings import APP_ROOT, EXAMPLES_DIR, OCR_FILE_EXTENSION, Settings
from .step_ocr import step_ocr
from .step_segmentation import step_segmentation
from .step_references_detection import step_references_detection
from .step_references_resolution import (
    step_legifrance_references_resolution,
    step_eurlex_references_resolution,
)
from .step_consolidation import step_consolidation
from .law_data.apis.legifrance import initialize_legifrance_client
from .law_data.apis.eurlex import initialize_eurlex_client
from .law_data.apis.mistral import initialize_mistral_client
from .errors import ArretifyError, ErrorCodes, DependencyError, SettingsError
from .pipeline import run_pipeline, load_ocr_file, load_pdf_file, save_html_file, PipelineStep
from .clean_ocrized_file import clean_ocrized_file
from .utils.files import is_pdf_path, is_ocr_path


_LOGGER = logging.getLogger("arretify")


def main(args: List[str]) -> None:
    parser = OptionParser()
    parser.add_option(
        "-i",
        "--input",
        help="Input folder or single file path.",
        default=EXAMPLES_DIR / "arretes_ocr",
    )
    parser.add_option(
        "-o",
        "--output",
        default=EXAMPLES_DIR / "arretes_html",
    )
    parser.add_option(
        "-v",
        "--verbose",
        action="store_true",
        default=False,
        help="Enable verbose logging.",
    )
    (options, args) = parser.parse_args(args=args)

    # ---------------- Initialization ---------------- #
    # Initialize environment variables before anything else
    load_dotenv()

    # Then initialize logging, so we don't miss any messages
    _initialize_root_logger(_LOGGER, options.verbose)

    session_context = SessionContext(
        settings=Settings.from_env(),
    )
    input_path = Path(options.input)
    output_path = Path(options.output)
    features = _Features()
    was_ocr_disabled_warning_given = False

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
    if input_path.is_dir():
        if not output_path.is_dir():
            _LOGGER.error(f"Expected output to be a directory, got {output_path}")

        all_input_file_paths = _walk_input_dir(input_path)
        for i, (relative_root, input_file_path) in enumerate(all_input_file_paths):
            output_root = output_path / relative_root
            output_root.mkdir(parents=True, exist_ok=True)
            html_file_path = output_root / f"{input_file_path.stem}.html"

            _LOGGER.info(
                f"\n\n[{i + 1}/{len(all_input_file_paths)}] processing {input_file_path} ..."
            )

            if is_pdf_path(input_file_path) and features.ocr is False:
                if not was_ocr_disabled_warning_given:
                    _ocr_disabled_warning()
                    was_ocr_disabled_warning_given = True

                _LOGGER.warning(
                    f"Skipping {input_file_path} because it is a PDF "
                    "and OCR support is not enabled."
                )
                continue

            try:
                _process_file(
                    session_context,
                    input_file_path,
                    html_file_path,
                    features,
                )
            except Exception:
                _LOGGER.error(
                    f"[{i + 1}/{len(all_input_file_paths)}] FAILED : {input_file_path} ..."
                )
                error_traceback = traceback.format_exc()
                _LOGGER.error(f"Traceback:\n{error_traceback}")

    else:
        if is_pdf_path(input_path) and features.ocr is False:
            _ocr_disabled_warning()
            _LOGGER.error(
                f"Failed to process {input_path} because it is a PDF "
                "and OCR support is not enabled."
            )
            sys.exit(1)

        _process_file(
            session_context,
            input_path,
            output_path,
            features,
        )


def _walk_input_dir(
    dir_path: Path,
) -> List[Tuple[Path, Path]]:
    pairs: List[Tuple[Path, Path]] = []
    for root, _, file_names in dir_path.walk():
        file_paths = [
            root / file_name
            for file_name in file_names
            if is_ocr_path(Path(file_name)) or is_pdf_path(Path(file_name))
        ]
        for file_path in file_paths:
            pairs.append((root.relative_to(dir_path), file_path))

    # Sort the files to ensure consistent order (useful for snapshot testing)
    return sorted(pairs, key=lambda x: x[1].name)


@dataclass(frozen=True)
class _Features:
    ocr: bool = False
    legifrance: bool = False
    eurlex: bool = False


def _process_file(
    session_context: SessionContext,
    input_path: Path,
    output_path: Path,
    features: _Features,
) -> None:
    pipeline_steps: List[PipelineStep] = [
        clean_ocrized_file,
        step_segmentation,
        step_references_detection,
    ]

    if features.legifrance:
        pipeline_steps.append(step_legifrance_references_resolution)
    if features.eurlex:
        pipeline_steps.append(step_eurlex_references_resolution)
    pipeline_steps.append(step_consolidation)

    parsing_context: ParsingContext
    if is_pdf_path(input_path):
        if not features.ocr:
            raise RuntimeError("OCR is disabled.")
        pipeline_steps.insert(0, step_ocr)
        parsing_context = load_pdf_file(
            session_context,
            input_path,
        )
    elif is_ocr_path(input_path):
        parsing_context = load_ocr_file(
            session_context,
            input_path,
        )
    else:
        raise ValueError(
            f"Unsupported file type: {input_path.suffix}. "
            f"Expected .pdf or .{OCR_FILE_EXTENSION} file."
        )

    save_html_file(
        output_path,
        run_pipeline(
            parsing_context,
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


def _initialize_root_logger(logger: logging.Logger, verbose: bool) -> None:
    # Configure root logger
    log_dir = APP_ROOT / "logs"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(_MainLoggingFormatter())

    logging.basicConfig(
        level=logging.WARNING,
        handlers=[stream_handler, logging.FileHandler(log_file, encoding="utf-8")],
    )

    # Set level globally based on verbosity flag
    if verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)


if __name__ == "__main__":
    main(sys.argv[1:])
