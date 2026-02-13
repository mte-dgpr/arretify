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
    _compute_structure_similarity,
    _get_table_structure_html,
    _get_table_text_content,
    _match_tables_by_page,
    _normalize_table_tag,
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


class TestComputeStructureSimilarity(unittest.TestCase):
    def test_identical_tables(self):
        # Arrange
        html1 = "<table><tr><th>H1</th><th>H2</th></tr><tr><td>C1</td><td>C2</td></tr></table>"
        html2 = "<table><tr><th>H1</th><th>H2</th></tr><tr><td>C1</td><td>C2</td></tr></table>"

        # Act
        similarity = _compute_structure_similarity(html1, html2)

        # Assert
        assert similarity == 1.0

    def test_different_structures(self):
        # Arrange
        html1 = "<table><tr><th>H1</th><th>H2</th></tr><tr><td>C1</td><td>C2</td></tr></table>"
        html2 = "<table><tr><th>H1</th></tr><tr><td>C1</td></tr></table>"

        # Act
        similarity = _compute_structure_similarity(html1, html2)

        # Assert
        assert similarity < 1.0


class TestGetTableStructureWithoutText(unittest.TestCase):
    def test_removes_text_content(self):
        # Arrange
        soup = BeautifulSoup(
            "<table><tr><th>Header</th></tr><tr><td>Data</td></tr></table>", "html.parser"
        )
        table = soup.find("table")

        # Act
        result = _get_table_structure_html(str(table))

        # Assert
        assert result == "<table><tr><th></th></tr><tr><td></td></tr></table>"


class TestMatchTablesByPage(unittest.TestCase):
    def test_matches_tables_with_high_text_similarity(self):
        # Arrange
        ground_truth = TablesData(
            tables_by_page={
                0: [
                    "<table><tr><td>Product A</td><td>100</td></tr></table>",
                    "<table><tr><td>Product B</td><td>200</td></tr></table>",
                ]
            }
        )
        result = TablesData(
            tables_by_page={
                0: [
                    "<table><tr><td>Product A</td><td>100</td></tr></table>",
                    "<table><tr><td>Product B</td><td>200</td></tr></table>",
                ]
            }
        )

        # Act
        matched_pairs, false_negatives, false_positives = _match_tables_by_page(
            ground_truth, result
        )

        # Assert
        assert matched_pairs == [
            (
                "<table><tr><td>Product A</td><td>100</td></tr></table>",
                "<table><tr><td>Product A</td><td>100</td></tr></table>",
            ),
            (
                "<table><tr><td>Product B</td><td>200</td></tr></table>",
                "<table><tr><td>Product B</td><td>200</td></tr></table>",
            ),
        ]
        assert false_negatives == []
        assert false_positives == []

    def test_returns_false_negative_when_result_page_missing(self):
        # Arrange
        ground_truth = TablesData(tables_by_page={0: ["<table><tr><td>Data</td></tr></table>"]})
        result = TablesData(tables_by_page={})

        # Act
        matched_pairs, false_negatives, false_positives = _match_tables_by_page(
            ground_truth, result
        )

        # Assert
        assert matched_pairs == []
        assert false_negatives == ["<table><tr><td>Data</td></tr></table>"]
        assert false_positives == []

    def test_ignores_low_similarity_tables(self):
        # Arrange
        ground_truth = TablesData(
            tables_by_page={0: ["<table><tr><td>Product A</td></tr></table>"]}
        )
        result = TablesData(
            tables_by_page={0: ["<table><tr><td>Completely Different</td></tr></table>"]}
        )

        # Act
        matched_pairs, false_negatives, false_positives = _match_tables_by_page(
            ground_truth, result
        )

        # Assert
        assert matched_pairs == []
        assert false_negatives == ["<table><tr><td>Product A</td></tr></table>"]
        assert false_positives == ["<table><tr><td>Completely Different</td></tr></table>"]


class TestGetTableStructureHtml(unittest.TestCase):
    def test_removes_text_and_preserves_structure_with_attributes(self):
        # Arrange
        table_html = (
            '<table><tr><th>Header Text</th><td colspan="2" rowspan="3">Cell Data</td></tr></table>'
        )

        # Act
        result = _get_table_structure_html(table_html)

        # Assert
        assert result == '<table><tr><th></th><td colspan="2" rowspan="3"></td></tr></table>'


class TestComputeEvaluation(unittest.TestCase):
    def test_perfect_match_returns_all_ones(self):
        # Arrange
        tables_data = TablesData(tables_by_page={0: ["<table><tr><td>Data</td></tr></table>"]})

        # Act
        metrics, _ = compute_metric_scores(tables_data, tables_data)

        # Assert
        assert metrics == {
            "recall": 1.0,
            "precision": 1.0,
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


class TestGetTableTextContent(unittest.TestCase):
    def test_extracts_concatenated_text_with_space_separator(self):
        # Arrange
        table_html = """
        <table>
            <tr>
                <th>Product</th>
                <th>Price</th>
            </tr>
            <tr>
                <td>Apple</td>
                <td>$2.50</td>
            </tr>
            <tr>
                <td>Orange</td>
                <td>$3.00</td>
            </tr>
        </table>
        """

        # Act
        result = _get_table_text_content(table_html)

        # Assert
        assert result == "Product Price Apple $2.50 Orange $3.00"
