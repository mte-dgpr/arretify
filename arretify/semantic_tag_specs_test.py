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

from bs4 import BeautifulSoup

from arretify.semantic_tag_specs import (
    DocumentReferenceData,
    SectionTitleData,
    _make_section_title_tag,
)
from arretify.types import DocumentType


class TestDocumentReferenceDataValidation(unittest.TestCase):
    def test_valid_year(self):
        # ARRANGE
        doc_type = DocumentType.eu_regulation
        date_year = "2020"
        # ACT
        document_reference_data = DocumentReferenceData(type=doc_type, date=date_year)
        # ASSERT
        self.assertEqual(document_reference_data.date, "2020")

    def test_valid_date(self):
        # ARRANGE
        doc_type = DocumentType.arrete_prefectoral
        date_full = "2020-02-11"
        # ACT
        document_reference_data = DocumentReferenceData(type=doc_type, date=date_full)
        # ASSERT
        self.assertEqual(document_reference_data.date, "2020-02-11")

    def test_invalid_year(self):
        # ARRANGE
        doc_type = DocumentType.eu_regulation
        not_a_year = "2020-02-11"
        # ACT & ASSERT
        with self.assertRaises(ValueError):
            DocumentReferenceData(type=doc_type, date=not_a_year)

    def test_invalid_date(self):
        # ARRANGE
        doc_type = DocumentType.arrete_prefectoral
        not_a_date = "2020"
        # ACT & ASSERT
        with self.assertRaises(ValueError):
            DocumentReferenceData(type=doc_type, date=not_a_date)


class TestSectionTitleTag(unittest.TestCase):

    def setUp(self):
        self.soup = BeautifulSoup("", "html.parser")

    def test_section_title_h2_to_h6(self):
        # ARRANGE
        data = SectionTitleData(level=0)
        # ACT
        tag = _make_section_title_tag(self.soup, data)
        # ASSERT
        self.assertEqual(tag.name, "h2")

    def test_section_title_h6(self):
        # ARRANGE
        data = SectionTitleData(level=4)
        # ACT
        tag = _make_section_title_tag(self.soup, data)
        # ASSERT
        self.assertEqual(tag.name, "h6")

    def test_section_title_div_aria_level(self):
        # ARRANGE
        data = SectionTitleData(level=5)
        # ACT
        tag = _make_section_title_tag(self.soup, data)
        # ASSERT
        self.assertEqual(tag.name, "div")
        self.assertEqual(tag.attrs.get("aria-level"), "7")
