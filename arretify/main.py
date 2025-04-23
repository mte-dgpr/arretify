from typing import Iterator, Tuple
from pathlib import Path
from optparse import OptionParser
import traceback

from bs4 import BeautifulSoup

from .settings import TEST_DATA_DIR, LOGGER, OCR_FILE_EXTENSION
from .step_segmentation import step_segmentation
from .step_references_detection import step_references_detection
from .step_references_resolution import step_references_resolution
from .step_consolidation import step_consolidation

from .clean_ocrized_file import clean_ocrized_file
from .parsing_utils.source_mapping import (
    initialize_lines,
    TextSegments,
)


def ocrized_arrete_to_html(lines: TextSegments) -> BeautifulSoup:
    lines = clean_ocrized_file(lines)
    soup = step_segmentation(lines)
    soup = step_references_detection(soup)
    soup = step_references_resolution(soup)
    soup = step_consolidation(soup)
    return soup


def main(input_path: Path, output_path: Path):
    with open(input_path, "r", encoding="utf-8") as f:
        raw_lines = f.readlines()
    lines = initialize_lines(raw_lines)
    soup = ocrized_arrete_to_html(lines)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(soup.prettify())


def _walk_ocrized_files(
    dir_path: Path,
) -> Iterator[Tuple[Path, Path]]:
    for root, _, file_names in input_path.walk():
        ocrized_file_paths = [
            root / file_name for file_name in file_names if file_name.endswith(OCR_FILE_EXTENSION)
        ]
        for ocrized_file_path in ocrized_file_paths:
            yield root.relative_to(dir_path), ocrized_file_path


if __name__ == "__main__":
    PARSER = OptionParser()
    PARSER.add_option(
        "-i",
        "--input",
        help="Input folder or single file path.",
        default=TEST_DATA_DIR / "arretes_ocr",
    )
    PARSER.add_option(
        "-o",
        "--output",
        default=TEST_DATA_DIR / "arretes_html",
    )
    (options, args) = PARSER.parse_args()

    input_path = Path(options.input)
    output_path = Path(options.output)

    if input_path.is_dir():
        if not output_path.is_dir():
            LOGGER.error(f"Expected output to be a directory, got {output_path}")
        ocrized_files_walk = list(_walk_ocrized_files(input_path))
        for i, (relative_root, ocrized_file_path) in enumerate(ocrized_files_walk):
            output_root = output_path / relative_root
            # Makes sure output dir exists
            output_root.mkdir(parents=True, exist_ok=True)
            html_file_path = output_root / f"{ocrized_file_path.stem}.html"
            LOGGER.info(f"[{i + 1}/{len(ocrized_files_walk)}] parsing {ocrized_file_path} ...")
            try:
                main(ocrized_file_path, html_file_path)
            except Exception:
                LOGGER.error(
                    f"[{i + 1}/{len(ocrized_files_walk)}] FAILED : {ocrized_file_path} ..."
                )
                error_traceback = traceback.format_exc()
                LOGGER.error(f"Traceback:\n{error_traceback}")

    else:
        main(input_path, output_path)
