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
import argparse
import logging
from pathlib import Path

import Levenshtein
from pydantic import BaseModel

from arretify.semantic_tag_specs import AppendixSpec, MainSpec, SectionData, SectionSpec
from arretify.types import ProtectedSoup, ProtectedTag
from arretify.utils.html_semantic import get_semantic_tag_data, is_semantic_tag
from quality_evaluation.common import (
    Evaluation,
    Run,
    add_evaluation_arguments,
    create_base_parser,
    create_evaluation_with_delta,
    dump_json,
    initialize_session_context,
    load_all_pdfs,
    load_json,
    load_or_create_experiment,
    log_evaluation_summary,
    prepare_current_run,
)

_LOGGER = logging.getLogger(Path(__file__).stem)
ROOT_DIR = Path(__file__).parent.parent
METRIC_NAME = "sections_similarity"

# -------------------- Data Models -------------------- #


class SectionTreeNode(BaseModel):
    data: SectionData
    children: list["SectionTreeNode"]


class SectionTree(BaseModel):
    main: list[SectionTreeNode]
    appendix: list[SectionTreeNode] | None


# -------------------- Section Tree Building -------------------- #


def build_section_tree(soup: ProtectedSoup) -> SectionTree:
    main_tag: ProtectedTag | None = None
    appendix_tag: ProtectedTag | None = None
    for child in soup.body.contents:
        if is_semantic_tag(child, spec_in=[MainSpec]):
            main_tag = child
        elif is_semantic_tag(child, spec_in=[AppendixSpec]):
            appendix_tag = child
    if main_tag is None:
        raise ValueError(f"'{MainSpec.tag_name}' semantic tag was not found.")

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


def compute_evaluation(
    file_name: str,
    section_tree_result: SectionTree,
    section_tree_ground_truth: SectionTree,
    baseline_run: Run | None,
) -> tuple[Evaluation, tuple[str, str]]:
    string_result = _generate_string_for_section_tree(section_tree_result)
    string_ground_truth = _generate_string_for_section_tree(section_tree_ground_truth)
    similarity = Levenshtein.ratio(string_result, string_ground_truth)

    return create_evaluation_with_delta(
        file_name=file_name,
        value=similarity,
        baseline_run=baseline_run,
        metric_name=METRIC_NAME,
    ), (string_result, string_ground_truth)


# -------------------- Main Script -------------------- #


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
    )
    logging.getLogger("arretify").setLevel(logging.ERROR)

    # ----- Parsing command-line arguments
    parser = argparse.ArgumentParser()
    parent_parser = create_base_parser(
        default_input=ROOT_DIR / "datasets" / "quality_evaluation",
        default_output=ROOT_DIR / "quality_evaluation" / "segmentation_in_sections.json",
    )

    subparsers = parser.add_subparsers(dest="action", required=True, help="Action to perform")

    generate_sections_parser = subparsers.add_parser(
        "generate_ground_truth",
        parents=[parent_parser],
        help="Generate section trees from HTML files",
    )

    evaluate_parser = subparsers.add_parser(
        "evaluate",
        parents=[parent_parser],
        help="Evaluate system output against ground truth",
    )
    add_evaluation_arguments(
        evaluate_parser,
        default_ground_truth=ROOT_DIR
        / "datasets"
        / "quality_evaluation"
        / "ground_truth_segmentation_in_sections",
    )

    args = parser.parse_args()

    # ----- Loading configuration and documents
    input_dir = Path(args.input)
    if not input_dir.is_dir():
        parser.error("Input path must be a directory.")
    _LOGGER.info(f"Input path: {input_dir}")

    cache_dir = Path(args.cache_dir) if args.cache_dir else None
    if cache_dir:
        cache_dir.mkdir(parents=True, exist_ok=True)
        _LOGGER.info(f"Cache directory: {cache_dir}")

    session_context = initialize_session_context()
    loaded_pdfs = load_all_pdfs(session_context, input_dir, cache_dir=cache_dir)

    # ----- Performing the requested action
    if args.action == "generate_ground_truth":
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)
        _LOGGER.info(f"Output directory: {output_dir}")
        for pdf_file_path, document_context in loaded_pdfs:
            section_tree = build_section_tree(document_context.soup)
            output_json_path = output_dir / f"{pdf_file_path.stem}.json"
            dump_json(output_json_path, section_tree)
            _LOGGER.info(f"Ground truth saved to: {output_json_path}")

    elif args.action == "evaluate":
        output_path = Path(args.output)
        _LOGGER.info(f"Output path: {output_path}")
        ground_truth_dir = Path(args.ground_truth)
        if not ground_truth_dir.is_dir():
            parser.error("Ground truth path must be a directory.")

        experiment = load_or_create_experiment(output_path)
        current_run, baseline_run = prepare_current_run(experiment)

        current_run.evaluation_sets[METRIC_NAME] = {}

        diff_dir = Path(args.diff_dir) if args.diff_dir else None
        if diff_dir:
            diff_dir.mkdir(parents=True, exist_ok=True)
            _LOGGER.info(f"Diff directory: {diff_dir}")

        for pdf_file_path, document_context in loaded_pdfs:
            section_tree_result = build_section_tree(document_context.soup)
            section_tree_ground_truth = load_json(
                ground_truth_dir / f"{pdf_file_path.stem}.json", SectionTree
            )
            evaluation, (string_result, string_ground_truth) = compute_evaluation(
                pdf_file_path.name,
                section_tree_result,
                section_tree_ground_truth,
                baseline_run,
            )
            current_run.evaluation_sets[METRIC_NAME][pdf_file_path.name] = evaluation

            if diff_dir:
                # Save ground truth and result as separate files for VS Code diff view
                ground_truth_file = diff_dir / f"{pdf_file_path.stem}.ground_truth.txt"
                result_file = diff_dir / f"{pdf_file_path.stem}.result.txt"
                ground_truth_file.write_text(string_ground_truth, encoding="utf-8")
                result_file.write_text(string_result, encoding="utf-8")
                _LOGGER.info(f"Diff files saved: {ground_truth_file.name} vs {result_file.name}")

        # ----- Generate evaluation summary
        log_evaluation_summary(current_run, baseline_run, METRIC_NAME)
        dump_json(output_path, experiment)
        _LOGGER.info(f"Experiment saved to: {output_path}")
