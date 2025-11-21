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
import unittest
from datetime import date

from .dates import parse_date_str, parse_year_str, render_date_str, render_year_str


class TestStrToDateAndDateToStr(unittest.TestCase):
    def test_parse_date_str(self):
        assert parse_date_str("1997-09-12") == date(year=1997, month=9, day=12)

    def test_render_date_str(self):
        assert render_date_str(date(year=2001, month=1, day=31)) == "2001-01-31"


class TestParseYearStrAndRenderYearStr(unittest.TestCase):
    def test_parse_year_2digits(self):
        assert parse_year_str("00") == 2000
        assert parse_year_str("99") == 1999

    def test_parse_year_4digits(self):
        assert parse_year_str("2000") == 2000
        assert parse_year_str("1999") == 1999

    def test_render_year_str(self):
        assert render_year_str(2000) == "2000"
        assert render_year_str(1999) == "1999"
