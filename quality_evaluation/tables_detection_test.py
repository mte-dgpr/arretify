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

from arretify.utils.testing import BaseTestCaseHtml
from quality_evaluation.tables_detection import (
    TablesData,
    _get_table_structure_html,
    _normalize_table_tag,
    _process_tables,
    compute_metric_scores,
    extract_tables_from_html,
)


class TestExtractTablesFromHtml(BaseTestCaseHtml):
    def test_extract_simple_table_with_page_separator(self):
        # Arrange
        html = """
        <html>
            <body>
                <a data-spec="page_separator" data-page_index="3"></a>
                <table>
                    <tr>
                        <th>Header 1</th>
                        <th>Header 2</th>
                    </tr>
                    <tr>
                        <td>Cell 1</td>
                        <td>Cell 2</td>
                    </tr>
                </table>
            </body>
        </html>
        """
        self.soup_extend(BeautifulSoup(html, "html.parser").contents)

        # Act
        result = extract_tables_from_html(self.context)

        # Assert
        expected = TablesData(
            tables_by_page={
                4: [
                    (
                        "<table>"
                        "<tr>"
                        "<th>Header 1</th>"
                        "<th>Header 2</th>"
                        "</tr>"
                        "<tr>"
                        "<td>Cell 1</td>"
                        "<td>Cell 2</td>"
                        "</tr>"
                        "</table>"
                    )
                ]
            }
        )
        assert result == expected


class TestGetTableStructureWithoutText(unittest.TestCase):
    def test_removes_text_content(self):
        # Arrange
        soup = BeautifulSoup(
            "<table><tr><th>Header</th></tr><tr><td>Data</td></tr></table>", "html.parser"
        )
        table = soup.find("table")

        # Act
        result = _get_table_structure_html(table)

        # Assert
        assert str(result) == "<table><tr><th></th></tr><tr><td></td></tr></table>"


class TestGetTableStructureHtml(unittest.TestCase):
    def test_removes_text_and_preserves_structure_with_attributes(self):
        # Arrange
        table_html = (
            '<table><tr><th>Header Text</th><td colspan="2" rowspan="3">Cell Data</td></tr></table>'
        )
        soup = BeautifulSoup(table_html, "html.parser")
        table = soup.find("table")

        # Act
        result = _get_table_structure_html(table)

        # Assert
        assert str(result) == '<table><tr><th></th><td colspan="2" rowspan="3"></td></tr></table>'


class TestProcessTables(unittest.TestCase):
    def test_process_tables_normalizes_and_separates_structure(self):
        # Arrange
        tables_data = TablesData(
            tables_by_page={
                0: [
                    '<table><tr><td>Cell 1</td><td colspan="2">Cell 2</td></tr></table>',
                    "<table><tr><th>Header</th></tr><tr><td>Data</td></tr></table>",
                ],
                1: ["<table><tbody><tr><td>Page 2</td></tr></tbody></table>"],
            }
        )

        # Act
        structure_html, general_html = _process_tables(tables_data)

        # Assert - Structure HTML has no text content
        assert structure_html == (
            '<table><tr><td></td><td colspan="2"></td></tr></table>'
            "<table><tr><th></th></tr><tr><td></td></tr></table>"
            "<table><tr><td></td></tr></table>"
        )

        # Assert - General HTML has text content and is normalized
        assert general_html == (
            '<table><tr><td>Cell 1</td><td colspan="2">Cell 2</td></tr></table>'
            "<table><tr><th>Header</th></tr><tr><td>Data</td></tr></table>"
            "<table><tr><td>Page 2</td></tr></table>"
        )


class TestComputeEvaluation(unittest.TestCase):
    def test_perfect_match_returns_all_ones(self):
        # Arrange
        tables_data = TablesData(tables_by_page={0: ["<table><tr><td>Data</td></tr></table>"]})

        # Act
        metrics, _ = compute_metric_scores(tables_data, tables_data)

        # Assert
        assert metrics == {
            "structure_accuracy": 1.0,
            "general_accuracy": 1.0,
        }


class TestNormalizeTableTag(unittest.TestCase):
    def test_normalize_table_tag_removes_attributes_except_colspan_rowspan(self):
        # Arrange
        html = """
        <table class="my-table" id="table1" style="width: 100%">
            <tr class="header-row">
                <th colspan="2" style="font-weight: bold">Header   Spacing</th>
                <th rowspan="3" class="special">Another</th>
            </tr>
            <tr>
                <td id="cell1" data-value="123">Cell  with   spaces</td>
                <td style="color: red">Normal
                    cell</td>
            </tr>
        </table>
        """
        soup = BeautifulSoup(html, "html.parser")
        table_tag = soup.find("table")

        # Act
        result = _normalize_table_tag(table_tag)

        # Assert
        expected = (
            "<table>"
            "<tr>"
            '<th colspan="2">Header Spacing</th>'
            '<th rowspan="3">Another</th>'
            "</tr>"
            "<tr>"
            "<td>Cell with spaces</td>"
            "<td>Normal cell</td>"
            "</tr>"
            "</table>"
        )
        assert str(result) == expected

    def test_replaces_br_with_space(self):
        # Arrange
        html = """
        <table>
            <tr>
                <td>Line 1<br/>Line 2<br/>Line 3</td>
                <td>Normal cell</td>
            </tr>
        </table>
        """
        soup = BeautifulSoup(html, "html.parser")
        table_tag = soup.find("table")

        # Act
        normalized = _normalize_table_tag(table_tag)
        cell_text = normalized.find("td").get_text()

        # Assert
        self.assertEqual(cell_text, "Line 1 Line 2 Line 3")

    def test_removes_thead_tbody_tags(self):
        # Arrange
        html = (
            "<table><thead><tr><th>Header</th></tr></thead>"
            "<tbody><tr><td>Data</td></tr></tbody></table>"
        )
        soup = BeautifulSoup(html, "html.parser")
        table_tag = soup.find("table")

        # Act
        result = _normalize_table_tag(table_tag)

        # Assert
        assert str(result) == "<table><tr><th>Header</th></tr><tr><td>Data</td></tr></table>"
