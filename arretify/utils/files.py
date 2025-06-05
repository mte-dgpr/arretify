from pathlib import Path

from arretify.settings import OCR_FILE_EXTENSION


def is_pdf_path(file_path: Path) -> bool:
    return file_path.suffix.lower() == ".pdf"


def is_ocr_path(file_path: Path) -> bool:
    return file_path.suffix.lower() == OCR_FILE_EXTENSION
