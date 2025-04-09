from pathlib import Path
import traceback

from .settings import TMP_DATA_DIR, LOGGER
from .main import ocrized_arrete_to_html
from .parsing_utils.source_mapping import initialize_lines


def main_single(input_file: Path):
    try:
        LOGGER.info(f"Processing file: {input_file}")
        with open(input_file, 'r', encoding='utf-8') as f:
            raw_lines = f.readlines()

        lines = initialize_lines(raw_lines)
        soup = ocrized_arrete_to_html(lines)

        TMP_DATA_DIR.mkdir(parents=True, exist_ok=True)
        output_file = TMP_DATA_DIR / f"{input_file.stem}.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(soup.prettify())

        LOGGER.info(f"Output written to: {output_file}")
    except Exception as e:
        LOGGER.error(f"Error while processing {input_file}")
        error_traceback = traceback.format_exc()
        LOGGER.error(f"Traceback:\n{error_traceback}")
        print(error_traceback)


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python main_single.py <path_to_ocr_file>")
    else:
        input_path = Path(sys.argv[1])
        if not input_path.exists():
            print(f"Input file does not exist: {input_path}")
        else:
            main_single(input_path)
