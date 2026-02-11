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
from copy import copy
from pathlib import Path

import Levenshtein
from bs4 import BeautifulSoup, Tag
from pydantic import BaseModel

from arretify.semantic_tag_specs import PageSeparatorSpec
from arretify.types import DocumentContext
from arretify.utils.html_semantic import get_semantic_tag_data, is_semantic_tag
from quality_evaluation.math_utils import compute_average_score
from quality_evaluation.types import MetricScores

ROOT_DIR = Path(__file__).parent.parent


# -------------------- Data Models -------------------- #


HtmlStr = str


class TablesData(BaseModel):
    """Container for tables organized by page."""

    tables_by_page: dict[int, list[HtmlStr]]
    """Mapping of page index to list of table HTML strings."""


# -------------------- Table Detection -------------------- #


def _strip_table_attrs(table_tag: Tag) -> Tag:
    """
    Strip all attributes from table HTML except colspan and rowspan.
    Also normalizes text content by stripping and collapsing whitespace.
    Returns cleaned HTML string.
    """
    table_copy = copy(table_tag)
    attrs_to_keep = {"colspan", "rowspan"}

    for tag in [table_copy, *table_copy.find_all(True)]:
        for attr in list(tag.attrs.keys()):
            if attr not in attrs_to_keep:
                del tag[attr]

        if tag.name in ["td", "th"]:
            text = tag.get_text(strip=True)
            text = " ".join(text.split())
            tag.clear()
            tag.string = text

    return table_copy


def extract_tables_from_html(document_context: DocumentContext) -> TablesData:
    """
    Extract tables from HTML document as stripped HTML strings.
    Returns TablesData containing tables organized by page.
    """
    tables_by_page: dict[int, list[str]] = {}

    for table_tag in document_context.soup.find_all("table"):
        page = 0
        page_separator = table_tag.find_previous(
            lambda t: is_semantic_tag(t, spec_in=[PageSeparatorSpec])
        )
        if page_separator:
            page = get_semantic_tag_data(PageSeparatorSpec, page_separator).page_index

        if page not in tables_by_page:
            tables_by_page[page] = []
        tables_by_page[page].append(str(_strip_table_attrs(table_tag)))

    return TablesData(tables_by_page=tables_by_page)


# -------------------- Table Matching & Metrics -------------------- #


def _get_table_text_content(table_html: HtmlStr) -> HtmlStr:
    """
    Get concatenated text content of all cells in a table HTML string.
    """
    return BeautifulSoup(table_html, "html.parser").get_text(separator=" ", strip=True)


def _match_tables_by_page(
    ground_truth: TablesData, result: TablesData
) -> tuple[list[tuple[str, str]], list[str], list[str]]:
    """
    Match tables between ground truth and result using text content similarity.
    Returns tuple of (matched_pairs, false_negatives, false_positives):
    - matched_pairs: list of (ground_truth_html, result_html) pairs that matched
    - false_negatives: list of ground_truth tables that were not detected
    - false_positives: list of result tables that could not be matched to ground truth
    """
    SIMILARITY_THRESHOLD = 0.5
    matched_pairs: list[tuple[str, str]] = []
    false_negatives: list[str] = []
    false_positives: list[str] = []

    for page, ground_truth_tables in ground_truth.tables_by_page.items():
        result_tables = list(result.tables_by_page.get(page, []))

        for ground_truth_table in ground_truth_tables:
            ground_truth_content = _get_table_text_content(ground_truth_table)
            best_index, best_similarity = None, 0.0

            for index, result_table in enumerate(result_tables):
                similarity = Levenshtein.ratio(
                    ground_truth_content, _get_table_text_content(result_table)
                )
                if similarity > best_similarity:
                    best_index, best_similarity = index, similarity

            if best_index is not None and best_similarity > SIMILARITY_THRESHOLD:
                matched_pairs.append((ground_truth_table, result_tables.pop(best_index)))
            else:
                false_negatives.append(ground_truth_table)

        false_positives.extend(result_tables)

    return matched_pairs, false_negatives, false_positives


def _get_table_structure_html(table_html: str) -> str:
    """
    Extract table structure HTML without text content.
    Returns HTML string with only tags and attributes (colspan, rowspan), no cell text.
    """
    soup = BeautifulSoup(table_html, "html.parser")
    table = soup.find("table")
    if not table:
        raise ValueError("No <table> tag found in the provided HTML.")

    table_copy = copy(table)
    if not isinstance(table_copy, Tag):
        raise ValueError("Expected Tag after copy")
    for cell in table_copy.find_all(["td", "th"]):
        cell.clear()

    return str(table_copy)


def _compute_structure_similarity(ground_truth_html: str, result_html: str) -> float:
    """
    Compute structure similarity using Levenshtein distance on table HTML without text content.
    Returns a score between 0 and 1.
    """
    ground_truth_structure = _get_table_structure_html(ground_truth_html)
    result_structure = _get_table_structure_html(result_html)
    return Levenshtein.ratio(ground_truth_structure, result_structure)


def _compute_general_similarity(ground_truth_html: str, result_html: str) -> float:
    """
    Compute general accuracy using Levenshtein distance on full table HTML including text content.
    Returns a score between 0 and 1.
    """
    return Levenshtein.ratio(ground_truth_html, result_html)


# -------------------- String Generation & Similarity -------------------- #


def compute_metric_scores(
    tables_result: TablesData,
    tables_ground_truth: TablesData,
) -> tuple[MetricScores, tuple[str, str] | None]:
    """
    Compute evaluation metrics for table detection.
    """

    matched_pairs, _, _ = _match_tables_by_page(tables_ground_truth, tables_result)

    total_detected_tables = sum(len(tables) for tables in tables_result.tables_by_page.values())
    total_ground_truth_tables = sum(
        len(tables) for tables in tables_ground_truth.tables_by_page.values()
    )

    # Recall: proportion of ground truth tables that were detected
    recall = (
        len(matched_pairs) / total_ground_truth_tables if total_ground_truth_tables > 0 else 1.0
    )

    # Precision: proportion of detected tables that were correctly matched
    precision = len(matched_pairs) / total_detected_tables if total_detected_tables > 0 else 1.0

    # Structure accuracy for matched tables (HTML structure without text)
    average_structure = compute_average_score(matched_pairs, _compute_structure_similarity)

    # General accuracy for matched tables (full HTML with text)
    average_general = compute_average_score(matched_pairs, _compute_general_similarity)

    return (
        {
            "recall": recall,
            "precision": precision,
            "structure_accuracy": average_structure,
            "general_accuracy": average_general,
        },
        None,
    )
