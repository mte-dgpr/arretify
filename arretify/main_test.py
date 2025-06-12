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

from arretify.settings import (
    EXAMPLES_DIR,
)

from .main import main

ARRETES_OCR_DIR = EXAMPLES_DIR / "arretes_ocr"
ARRETES_HTML_DIR = EXAMPLES_DIR / "arretes_html"


class TestMain(unittest.TestCase):

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
