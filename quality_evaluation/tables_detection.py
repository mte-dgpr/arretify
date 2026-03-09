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
from quality_evaluation.types import ComputeMetricsResult

ROOT_DIR = Path(__file__).parent.parent


# -------------------- Data Models -------------------- #


HtmlStr = str


class TablesData(BaseModel):
    """Container for tables organized by page."""

    tables_by_page: dict[int, list[HtmlStr]]
    """Mapping of page index to list of table HTML strings."""


# -------------------- Table Detection -------------------- #


def _normalize_table_tag(table_tag: Tag) -> Tag:
    """
    Normalize a <table> tag by stripping whitespace, new lines
    and removing non-structural attributes.
    """
    table_copy = copy(table_tag)
    attrs_to_keep = {"colspan", "rowspan"}

    # Replace <br> tags with spaces
    for br_tag in table_copy.find_all("br"):
        br_tag.replace_with(" ")

    # Remove <thead> and <tbody> tags while keeping their contents
    for tag in table_copy.find_all(["thead", "tbody"]):
        tag.unwrap()

    for tag in [table_copy, *table_copy.find_all(True)]:
        # Remove all attributes except those in attrs_to_keep
        for attr in list(tag.attrs.keys()):
            if attr not in attrs_to_keep:
                del tag[attr]

        # Normalize text content in cells by stripping and collapsing whitespace
        if tag.name in ["td", "th"]:
            text = " ".join(tag.get_text().split()).strip()
            tag.clear()
            tag.string = text

    # Remove NavigableString elements that contain only whitespace/newlines
    for element in table_copy.find_all(string=lambda text: text.strip() == ""):
        element.extract()

    return table_copy


def extract_tables_from_html(document_context: DocumentContext) -> TablesData:
    """
    Extract tables from HTML document as stripped HTML strings.
    Returns TablesData containing tables organized by page.
    """
    tables_by_page: dict[int, list[str]] = {}

    for table_tag in document_context.soup.find_all("table"):
        page = 1
        page_separator = table_tag.find_previous(
            lambda t: is_semantic_tag(t, spec_in=[PageSeparatorSpec])
        )
        if page_separator:
            page = get_semantic_tag_data(PageSeparatorSpec, page_separator).page_index + 1

        if page not in tables_by_page:
            tables_by_page[page] = []
        tables_by_page[page].append(str(_normalize_table_tag(table_tag)))

    return TablesData(tables_by_page=tables_by_page)


# -------------------- Table Metrics -------------------- #


def _get_table_structure_html(table_tag: Tag) -> Tag:
    """
    Extract table structure from a table Tag without text content.
    Returns Tag with only tags and attributes (colspan, rowspan), no cell text.
    """
    table_copy = copy(table_tag)
    for cell in table_copy.find_all(["td", "th"]):
        cell.clear()

    return table_copy


def _process_tables(tables_data: TablesData) -> tuple[HtmlStr, HtmlStr]:
    """
    Process all tables from TablesData:
    1. Collect and normalize all tables
    2. Extract structure-only HTML for each table
    3. Concatenate into two strings: structure-only and full HTML

    Returns tuple of (structure_html, general_html)

    We concatenate all tables because it is difficult to match individual tables
    between result and ground truth, especially when there are extra or missing tables.
    Also there are problematic cases where a single table in the ground truth corresponds to
    multiple tables in the result or vice versa (if tables are split between pages for example).
    """
    all_tables_html: list[HtmlStr] = []
    all_structures_html: list[HtmlStr] = []

    for page in sorted(tables_data.tables_by_page.keys()):
        for table_html in tables_data.tables_by_page[page]:
            soup = BeautifulSoup(table_html, "html.parser")
            table_tag = soup.find("table")
            if not isinstance(table_tag, Tag):
                raise ValueError("Expected a single <table> tag in the HTML string.")

            normalized_table = _normalize_table_tag(table_tag)
            all_structures_html.append(str(_get_table_structure_html(normalized_table)))
            all_tables_html.append(str(normalized_table))

    return "".join(all_structures_html), "".join(all_tables_html)


# -------------------- String Generation & Similarity -------------------- #


def compute_metric_scores(
    tables_result: TablesData,
    tables_ground_truth: TablesData,
) -> ComputeMetricsResult:
    """
    Compute evaluation metrics for table detection.
    Concatenates all tables into single strings and compares them.
    """
    # Process all tables: normalize, extract structures, concatenate
    ground_truth_structure, ground_truth_general = _process_tables(tables_ground_truth)
    result_structure, result_general = _process_tables(tables_result)

    # Structure accuracy (HTML structure without text)
    structure_accuracy = Levenshtein.ratio(ground_truth_structure, result_structure)

    # General accuracy (full HTML with text)
    general_accuracy = Levenshtein.ratio(ground_truth_general, result_general)

    return (
        {
            "structure_accuracy": structure_accuracy,
            "general_accuracy": general_accuracy,
        },
        {
            "structure_accuracy": (result_structure, ground_truth_structure),
            "general_accuracy": (result_general, ground_truth_general),
        },
    )
