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
from pathlib import Path

import Levenshtein
from pydantic import BaseModel

from arretify.semantic_tag_specs import AppendixSpec, MainSpec, SectionData, SectionSpec
from arretify.types import DocumentContext, ProtectedTag
from arretify.utils.html_semantic import get_semantic_tag_data, is_semantic_tag
from quality_evaluation.types import ComputeMetricsResult

ROOT_DIR = Path(__file__).parent.parent

# -------------------- Data Models -------------------- #


class SectionTreeNode(BaseModel):
    data: SectionData
    children: list["SectionTreeNode"]


class SectionTree(BaseModel):
    main: list[SectionTreeNode]
    appendix: list[SectionTreeNode] | None


# -------------------- Section Tree Building -------------------- #


def build_section_tree(document_context: DocumentContext) -> SectionTree:
    main_tag: ProtectedTag | None = None
    appendix_tag: ProtectedTag | None = None
    assert (
        document_context.protected_soup.body is not None
    ), "Expected <body> tag in the HTML document."
    for child in document_context.protected_soup.body.contents:
        if is_semantic_tag(child, spec_in=[MainSpec]):
            main_tag = child
        elif is_semantic_tag(child, spec_in=[AppendixSpec]):
            appendix_tag = child
    if main_tag is None:
        raise ValueError(f"'{MainSpec.tag_name}' semantic tag was not found.")
    assert main_tag is not None

    main: list[SectionTreeNode] = [
        _build_section_subtree(child)
        for child in main_tag.contents
        if is_semantic_tag(child, spec_in=[SectionSpec])
    ]

    appendix: list[SectionTreeNode] | None = None
    if appendix_tag is not None:
        appendix = [
            _build_section_subtree(child)
            for child in appendix_tag.contents
            if is_semantic_tag(child, spec_in=[SectionSpec])
        ]

    return SectionTree(main=main, appendix=appendix)


def _build_section_subtree(section_tag: ProtectedTag) -> SectionTreeNode:
    children: list[SectionTreeNode] = []
    for child in section_tag.contents:
        if is_semantic_tag(child, spec_in=[SectionSpec]):
            children.append(_build_section_subtree(child))
    return SectionTreeNode(
        data=get_semantic_tag_data(SectionSpec, section_tag),
        children=children,
    )


# -------------------- String Generation & Similarity -------------------- #


def _normalize_section_tree_string(section_tree_string: str) -> str:
    if not section_tree_string:
        return ""
    lines: list[str] = section_tree_string.splitlines()
    max_line_length: int = max(len(line) for line in lines)
    for i, line in enumerate(lines):
        lines[i] = line.ljust(max_line_length)
    return "\n".join(lines)


def _generate_string_for_section_tree_node_list(
    children: list[SectionTreeNode], depth: int = 0
) -> str:
    result = ""
    indent = ">" * depth
    for child in children:
        result += f"{indent}{child.data.number}\n"
        result += _generate_string_for_section_tree_node_list(child.children, depth + 1)
    return result


def _generate_string_for_section_tree(section_tree: SectionTree) -> str:
    return (
        _normalize_section_tree_string(
            _generate_string_for_section_tree_node_list(section_tree.main)
        )
        + "\n-\n"
        + _normalize_section_tree_string(
            _generate_string_for_section_tree_node_list(section_tree.appendix or [])
        )
    )


def compute_metric_scores(
    section_tree_result: SectionTree,
    section_tree_ground_truth: SectionTree,
) -> ComputeMetricsResult:
    string_result = _generate_string_for_section_tree(section_tree_result)
    string_ground_truth = _generate_string_for_section_tree(section_tree_ground_truth)
    similarity = Levenshtein.ratio(string_result, string_ground_truth)
    return (
        {"sections_similarity": similarity},
        {"sections_similarity": (string_result, string_ground_truth)},
    )
