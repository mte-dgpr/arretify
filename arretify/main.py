from typing import Iterator, Tuple, List
from pathlib import Path
from optparse import OptionParser
import traceback
import logging
from datetime import datetime

from dotenv import load_dotenv

from bs4 import BeautifulSoup

from .types import ParsingContext, SessionContext
from .settings import APP_ROOT, TEST_DATA_DIR, OCR_FILE_EXTENSION, DEFAULT_ARRETE_TEMPLATE
from .utils.scripts import load_settings_from_env
from .step_segmentation import step_segmentation
from .step_references_detection import step_references_detection
from .step_references_resolution import step_references_resolution
from .step_consolidation import step_consolidation
from .clean_ocrized_file import clean_ocrized_file
from .parsing_utils.source_mapping import (
    initialize_lines,
)
from .law_data.apis.legifrance import initialize_legifrance_client
from .law_data.apis.eurlex import initialize_eurlex_client
from .errors import ArretifyError, ErrorCodes


_LOGGER = logging.getLogger("arretify")


def ocr_to_html(session_context: SessionContext, raw_lines: List[str]) -> ParsingContext:
    lines = initialize_lines(raw_lines)
    lines = clean_ocrized_file(lines)
    soup = BeautifulSoup(DEFAULT_ARRETE_TEMPLATE, features="html.parser")
    parsing_context = ParsingContext.from_session_context(
        session_context,
        lines=lines,
        soup=soup,
    )
    parsing_context = step_segmentation(parsing_context)
    parsing_context = step_references_detection(parsing_context)
    parsing_context = step_references_resolution(parsing_context)
    parsing_context = step_consolidation(parsing_context)

    return parsing_context


def ocr_file_to_html_file(settings, input_path: Path, output_path: Path):
    with open(input_path, "r", encoding="utf-8") as f:
        raw_lines = f.readlines()
    parsing_context = ocr_to_html(settings, raw_lines)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(parsing_context.soup.prettify())


def main():
    parser = OptionParser()
    parser.add_option(
        "-i",
        "--input",
        help="Input folder or single file path.",
        default=TEST_DATA_DIR / "arretes_ocr",
    )
    parser.add_option(
        "-o",
        "--output",
        default=TEST_DATA_DIR / "arretes_html",
    )
    parser.add_option(
        "-v",
        "--verbose",
        action="store_true",
        default=False,
        help="Enable verbose logging.",
    )
    (options, args) = parser.parse_args()

    # Load environment variables from .env file
    load_dotenv()

    # Initialize logging before anything else, so we get all logs
    _initialize_root_logger(_LOGGER, options.verbose)

    input_path = Path(options.input)
    output_path = Path(options.output)

    session_context = SessionContext(
        settings=load_settings_from_env(),
    )
    try:
        session_context = initialize_legifrance_client(session_context)
    except ArretifyError as error:
        if error.code is ErrorCodes.law_data_api_error:
            _LOGGER.warning("failed to initialize Legifrance client")
    session_context = initialize_eurlex_client(session_context)

    # Do the parsing
    if input_path.is_dir():
        if not output_path.is_dir():
            _LOGGER.error(f"Expected output to be a directory, got {output_path}")
        ocrized_files_walk = list(_walk_ocrized_files(input_path))
        for i, (relative_root, ocrized_file_path) in enumerate(ocrized_files_walk):
            output_root = output_path / relative_root
            # Makes sure output dir exists
            output_root.mkdir(parents=True, exist_ok=True)
            html_file_path = output_root / f"{ocrized_file_path.stem}.html"
            _LOGGER.info(f"\n\n[{i + 1}/{len(ocrized_files_walk)}] parsing {ocrized_file_path} ...")
            try:
                ocr_file_to_html_file(session_context, ocrized_file_path, html_file_path)
            except Exception:
                _LOGGER.error(
                    f"[{i + 1}/{len(ocrized_files_walk)}] FAILED : {ocrized_file_path} ..."
                )
                error_traceback = traceback.format_exc()
                _LOGGER.error(f"Traceback:\n{error_traceback}")

    else:
        ocr_file_to_html_file(session_context, input_path, output_path)


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
    main()
