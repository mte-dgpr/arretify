# Pour re-générer les snapshots HTML, voir README, section "Snapshot testing".
import unittest
from pathlib import Path
from tempfile import mkdtemp

from arretify.settings import (
    EXAMPLES_DIR,
)
from arretify.utils import html

from .main import main

ARRETES_OCR_DIR = EXAMPLES_DIR / "arretes_ocr"
ARRETES_HTML_DIR = EXAMPLES_DIR / "arretes_html"


class TestMain(unittest.TestCase):
    def setUp(self):
        html._ELEMENT_ID_COUNTER = 0

    def test_parse_arrete_snapshots(self):
        print("Testing snapshots")
        tmp_dir = Path(mkdtemp(prefix="arretify-testing-"))
        main(args=["--input", str(ARRETES_OCR_DIR), "--output", str(tmp_dir)])
        for relative_path in _iter_reference_html_files():
            print(f"Comparing {relative_path}")
            expected_contents = open(ARRETES_HTML_DIR / relative_path, "r", encoding="utf-8").read()
            actual_contents = open(tmp_dir / relative_path, "r", encoding="utf-8").read()
            assert actual_contents == expected_contents


def _iter_reference_html_files():
    arretes_html_paths = sorted(Path(ARRETES_HTML_DIR).rglob("*html"))
    for arrete_html_path in arretes_html_paths:
        yield arrete_html_path.relative_to(ARRETES_HTML_DIR)
