# Pour re-générer les snapshots HTML, voir README, section "Snapshot testing".
import unittest
import logging
from pathlib import Path

from arretify.settings import (
    TEST_DATA_DIR,
    OCR_FILE_EXTENSION,
)
from arretify.utils import html
from arretify.utils.testing import create_session_context

from .main import ocr_to_html

ARRETES_OCR_DIR = TEST_DATA_DIR / "arretes_ocr"
ARRETES_HTML_DIR = TEST_DATA_DIR / "arretes_html"
_LOGGER = logging.getLogger(__name__)


class TestMain(unittest.TestCase):
    def setUp(self):
        html._ID_COUNTER = 0

    def test_parse_arrete_snapshots(self):
        _LOGGER.info("Testing snapshots")
        for (
            arrete_ocr_file_path,
            actual_contents,
        ) in _iter_parsed_arretes_ocr_files():
            _LOGGER.info(
                f"Input {arrete_ocr_file_path.parent.name}/{arrete_ocr_file_path.stem} ..."
            )
            arrete_html_file_path = (
                ARRETES_HTML_DIR
                / f"{arrete_ocr_file_path.parent.name}/{arrete_ocr_file_path.stem}.html"
            )
            expected_contents = open(arrete_html_file_path, "r", encoding="utf-8").read()
            assert actual_contents == expected_contents


def _iter_parsed_arretes_ocr_files():
    arretes_ocr_file_paths = sorted(Path(ARRETES_OCR_DIR).rglob(f"*{OCR_FILE_EXTENSION}"))
    session_context = create_session_context()
    for arrete_ocr_file_path in arretes_ocr_file_paths:
        arrete_contents = open(arrete_ocr_file_path, "r", encoding="utf-8").readlines()
        parsing_context = ocr_to_html(session_context, arrete_contents)
        yield arrete_ocr_file_path, parsing_context.soup.prettify()
