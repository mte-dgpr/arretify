import sys
from typing import Iterator, Tuple, List
from pathlib import Path
from optparse import OptionParser
import traceback
import logging
from datetime import datetime

from dotenv import load_dotenv

from .types import SessionContext
from .settings import APP_ROOT, EXAMPLES_DIR, OCR_FILE_EXTENSION, DEFAULT_ARRETE_TEMPLATE, Settings
from .step_segmentation import step_segmentation
from .step_references_detection import step_references_detection
from .step_references_resolution import (
    step_legifrance_references_resolution,
    step_eurlex_references_resolution,
)
from .step_consolidation import step_consolidation
from .law_data.apis.legifrance import initialize_legifrance_client, MissingSettingsError
from .law_data.apis.eurlex import initialize_eurlex_client
from .errors import ArretifyError, ErrorCodes
from .pipeline import ocr_to_html, load_ocr_file, save_html_file, ParsingPipelineStep


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

    # Load environment variables from .env file
    load_dotenv()

    # Initialize logging before anything else, so we get all logs
    _initialize_root_logger(_LOGGER, options.verbose)

    # Initialize session context
    session_context = SessionContext(
        settings=Settings.from_env(),
    )

    # Initialize input and output paths
    input_path = Path(options.input)
    output_path = Path(options.output)

    # Initialize steps
    parsing_steps: List[ParsingPipelineStep] = [
        step_segmentation,
        step_references_detection,
    ]

    # Initialize reference resolution steps
    try:
        session_context = initialize_legifrance_client(session_context)
    except MissingSettingsError:
        _LOGGER.info(
            "Legifrance credentials not provided, skipping Legifrance references resolution"
        )
    except ArretifyError as error:
        if error.code is ErrorCodes.law_data_api_error:
            _LOGGER.warning("failed to initialize Legifrance client")
    else:
        _LOGGER.info("Legifrance references resolution is active")
        parsing_steps.append(step_legifrance_references_resolution)

    try:
        session_context = initialize_eurlex_client(session_context)
    except MissingSettingsError:
        _LOGGER.info("Eurlex credentials not provided, skipping Eurlex references resolution")
    else:
        _LOGGER.info("Eurlex references resolution is active")
        parsing_steps.append(step_eurlex_references_resolution)

    # Add consolidation step
    parsing_steps.append(step_consolidation)

    # Do the parsing
    if input_path.is_dir():
        if not output_path.is_dir():
            _LOGGER.error(f"Expected output to be a directory, got {output_path}")

        # Sort the files to ensure consistent order (useful for snapshot testing)
        ocrized_files_walk = sorted(_walk_ocrized_files(input_path), key=lambda x: x[1].name)
        for i, (relative_root, ocrized_file_path) in enumerate(ocrized_files_walk):
            output_root = output_path / relative_root
            # Makes sure output dir exists
            output_root.mkdir(parents=True, exist_ok=True)
            html_file_path = output_root / f"{ocrized_file_path.stem}.html"
            _LOGGER.info(f"\n\n[{i + 1}/{len(ocrized_files_walk)}] parsing {ocrized_file_path} ...")
            try:
                save_html_file(
                    html_file_path,
                    ocr_to_html(
                        session_context,
                        load_ocr_file(ocrized_file_path),
                        arrete_template=DEFAULT_ARRETE_TEMPLATE,
                        parsing_steps=parsing_steps,
                    ),
                )
            except Exception:
                _LOGGER.error(
                    f"[{i + 1}/{len(ocrized_files_walk)}] FAILED : {ocrized_file_path} ..."
                )
                error_traceback = traceback.format_exc()
                _LOGGER.error(f"Traceback:\n{error_traceback}")

    else:
        save_html_file(
            output_path,
            ocr_to_html(
                session_context,
                load_ocr_file(input_path),
                arrete_template=DEFAULT_ARRETE_TEMPLATE,
                parsing_steps=parsing_steps,
            ),
        )


def _walk_ocrized_files(
    dir_path: Path,
) -> Iterator[Tuple[Path, Path]]:
    for root, _, file_names in dir_path.walk():
        ocrized_file_paths = [
            root / file_name for file_name in file_names if file_name.endswith(OCR_FILE_EXTENSION)
        ]
        for ocrized_file_path in ocrized_file_paths:
            yield root.relative_to(dir_path), ocrized_file_path


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
