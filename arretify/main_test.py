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

# Pour re-générer les snapshots HTML, voir README, section "Snapshot testing".
import unittest
from pathlib import Path
from tempfile import mkdtemp

from arretify.settings import EXAMPLES_DIR

from .main import _walk_input_dir, main

ARRETES_OCR_DIR = EXAMPLES_DIR / "arretes_ocr"
ARRETES_HTML_DIR = EXAMPLES_DIR / "arretes_html"


class TestMain(unittest.TestCase):

    def test_parse_arrete_snapshots(self):
        print("Testing snapshots")
        tmp_dir = Path(mkdtemp(prefix="arretify-testing-"))
        main(args=["--recursive", "--input", str(ARRETES_OCR_DIR), "--output", str(tmp_dir)])
        for relative_path in _iter_reference_html_files():
            print(f"Comparing {relative_path}")
            expected_contents = open(ARRETES_HTML_DIR / relative_path, "r", encoding="utf-8").read()
            actual_contents = open(tmp_dir / relative_path, "r", encoding="utf-8").read()
            assert actual_contents == expected_contents


class TestWalkInputDir(unittest.TestCase):

    def test_iter_reference_html_files(self):
        paths = _walk_input_dir(ARRETES_OCR_DIR)
        assert paths == [
            ARRETES_OCR_DIR / "arrete_bilan_ars",
            ARRETES_OCR_DIR / "arrete_chambre_agriculture",
            ARRETES_OCR_DIR / "arrete_circulation",
            ARRETES_OCR_DIR / "arrete_nomination",
            ARRETES_OCR_DIR / "arrete_ppr",
            ARRETES_OCR_DIR / "arrete_rectorat",
            ARRETES_OCR_DIR / "arrete_sentiers_randonnee",
            ARRETES_OCR_DIR / "arretes_icpe/0003013459/2020-04-20",
            ARRETES_OCR_DIR / "arretes_icpe/0003013459/2021-09-24",
            ARRETES_OCR_DIR / "arretes_icpe/0003013459/2023-02-22",
            ARRETES_OCR_DIR / "arretes_icpe/0005302394/2008-12-10",
            ARRETES_OCR_DIR / "arretes_icpe/0005302394/2009-12-18",
            ARRETES_OCR_DIR / "arretes_icpe/0005302394/2010-12-24",
            ARRETES_OCR_DIR / "arretes_icpe/0005302394/2012-04-03",
            ARRETES_OCR_DIR / "arretes_icpe/0005302394/2012-12-07",
            ARRETES_OCR_DIR / "arretes_icpe/0005302394/2020-12-22",
            ARRETES_OCR_DIR / "arretes_icpe/0005800425/2003-09-09",
            ARRETES_OCR_DIR / "arretes_icpe/0005800425/2005-11-08",
            ARRETES_OCR_DIR / "arretes_icpe/0005800425/2007-04-19",
            ARRETES_OCR_DIR / "arretes_icpe/0005800425/2010-03-29",
            ARRETES_OCR_DIR / "arretes_icpe/0005800425/2012-09-03",
            ARRETES_OCR_DIR / "arretes_icpe/0005800425/2025-02-24",
            ARRETES_OCR_DIR / "arretes_icpe/0005804239/2009-12-08",
            ARRETES_OCR_DIR / "arretes_icpe/0005804239/2012-04-02",
            ARRETES_OCR_DIR / "arretes_icpe/0005804239/2014-01-09",
            ARRETES_OCR_DIR / "arretes_icpe/0005804239/2014-12-11",
            ARRETES_OCR_DIR / "arretes_icpe/0005804239/2020-04-30",
            ARRETES_OCR_DIR / "arretes_icpe/0005804239/2023-12-04",
            ARRETES_OCR_DIR / "arretes_icpe/0005804239/2024-09-27",
        ]


def _iter_reference_html_files():
    arretes_html_paths = sorted(Path(ARRETES_HTML_DIR).rglob("*html"))
    for arrete_html_path in arretes_html_paths:
        yield arrete_html_path.relative_to(ARRETES_HTML_DIR)
