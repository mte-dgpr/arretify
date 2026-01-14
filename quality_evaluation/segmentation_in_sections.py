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
from datetime import date as Date
from pathlib import Path
from typing import Type, TypeVar

import Levenshtein
from dotenv import load_dotenv
from pydantic import BaseModel

from arretify.law_data.apis.mistral import initialize_mistral_client
from arretify.pipeline import load_ocr_pages, load_pdf_file, run_pipeline
from arretify.semantic_tag_specs import AppendixSpec, MainSpec, SectionData, SectionSpec
from arretify.settings import Settings
from arretify.step_markdown_cleaning import step_markdown_cleaning
from arretify.step_ocr import step_ocr
from arretify.step_segmentation import step_segmentation
from arretify.types import DocumentContext, ProtectedSoup, ProtectedTag, SessionContext
from arretify.utils.html_semantic import get_semantic_tag_data, is_semantic_tag

_LOGGER = logging.getLogger(Path(__file__).stem)
ROOT_DIR = Path(__file__).parent.parent

# -------------------- Data Models -------------------- #


class SectionTreeNode(BaseModel):
    data: SectionData
    children: list["SectionTreeNode"]


class SectionTree(BaseModel):
    main: list[SectionTreeNode]
    appendix: list[SectionTreeNode] | None


class Evaluation(BaseModel):
    file_name: str
    similarity: float
    diff: float | None


class Run(BaseModel):
    date: Date
    baseline_date: Date | None
    evaluations: dict[str, Evaluation]


class Experiment(BaseModel):
    runs: list[Run]


T = TypeVar("T", bound=BaseModel)


def dump_json(output_json_path: Path, model: BaseModel) -> None:
    output_json_path.write_text(model.model_dump_json(indent=2), encoding="utf-8")


def load_json(json_path: Path, model_class: Type[T]) -> T:
    return model_class.model_validate_json(json_path.read_text(encoding="utf-8"))


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


def _generate_string_for_section_tree(children: list[SectionTreeNode]) -> str:
    result = ""
    for child in children:
        result += f"{child.data.number}\n"
        result += _generate_string_for_section_tree(child.children)
    return result


def compute_similarity(children1: list[SectionTreeNode], children2: list[SectionTreeNode]) -> float:
    return Levenshtein.ratio(
        _normalize_section_tree_string(_generate_string_for_section_tree(children1)),
        _normalize_section_tree_string(_generate_string_for_section_tree(children2)),
    )


def compute_evaluation(
    file_name: str,
    section_tree_actual: SectionTree,
    section_tree_ground_truth: SectionTree,
    baseline_run: Run | None,
) -> Evaluation:
    baseline_evaluation = None
    if baseline_run:
        baseline_evaluation = baseline_run.evaluations.get(file_name)
        if baseline_evaluation is None:
            _LOGGER.warning(
                f"No baseline evaluation found for {file_name} " f"in run dated {baseline_run.date}"
            )

    similarity = compute_similarity(section_tree_actual.main, section_tree_ground_truth.main)

    return Evaluation(
        file_name=file_name,
        similarity=similarity,
        diff=(
            similarity - baseline_evaluation.similarity if baseline_evaluation is not None else None
        ),
    )


# -------------------- File Loading and PDF Processing -------------------- #


def convert_pdf_to_html(
    session_context: SessionContext, pdf_file_path: Path, cache_dir: Path | None
) -> DocumentContext:
    if cache_dir is not None:
        ocr_pages_dir = cache_dir / pdf_file_path.stem

    if ocr_pages_dir and ocr_pages_dir.exists():
        if not ocr_pages_dir.is_dir():
            raise ValueError(f"Cache path {ocr_pages_dir} exists and is not a directory.")
        _LOGGER.info(f"Loading OCR pages from cache directory for {pdf_file_path.name}")
        return run_pipeline(
            load_ocr_pages(session_context, ocr_pages_dir),
            [step_markdown_cleaning, step_segmentation],
        )

    else:
        if ocr_pages_dir is not None:
            ocr_pages_dir.mkdir(parents=True, exist_ok=True)

        def step_ocr_with_cache(
            document_context: DocumentContext,
        ) -> DocumentContext:
            return step_ocr(
                document_context=document_context,
                ocr_pages_dir=ocr_pages_dir,
            )

        _LOGGER.info(f"Performing OCR for {pdf_file_path.name}")
        return run_pipeline(
            load_pdf_file(session_context, pdf_file_path),
            [step_ocr_with_cache, step_markdown_cleaning, step_segmentation],
        )


def load_all_pdfs(input_dir: Path, cache_dir: Path | None) -> list[tuple[Path, DocumentContext]]:
    pdf_file_paths: list[Path] = []
    for entry in input_dir.iterdir():
        if entry.is_file() and entry.suffix.lower() == ".pdf":
            pdf_file_paths.append(entry)
    loaded: list[tuple[Path, DocumentContext]] = []
    for pdf_file_path in sorted(pdf_file_paths):
        try:
            loaded.append(
                (
                    pdf_file_path,
                    convert_pdf_to_html(session_context, pdf_file_path, cache_dir=cache_dir),
                )
            )
        except Exception as e:
            _LOGGER.error(f"Error processing file {pdf_file_path}: {e}")
    return loaded


# -------------------- Main Script -------------------- #


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.ERROR,
        format="%(message)s",
    )
    _LOGGER.setLevel(logging.INFO)

    # ----- Parsing command-line arguments
    parser = argparse.ArgumentParser()
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument(
        "-i",
        "--input",
        required=True,
        help="Input folder.",
    )
    parent_parser.add_argument(
        "--cache-dir",
        default=None,
        help="Path to cache directory.",
    )
    parent_parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="Output path.",
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
    evaluate_parser.add_argument(
        "--ground-truth",
        default=ROOT_DIR
        / "datasets"
        / "quality_evaluation"
        / "ground_truth_segmentation_in_sections",
        help="Path to the directory containing ground truth section tree JSON files.",
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

    load_dotenv()
    session_context = SessionContext(
        settings=Settings.from_env(),
    )
    session_context = initialize_mistral_client(session_context)

    loaded_pdfs = load_all_pdfs(input_dir, cache_dir=cache_dir)

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

        if output_path.exists():
            experiment = load_json(output_path, Experiment)
            _LOGGER.info("Existing experiment loaded.")
        else:
            experiment = Experiment(runs=[])
            _LOGGER.info("New experiment will be created.")

        if any(run.date == Date.today() for run in experiment.runs):
            parser.error(
                "A run for today already exists."
                "Please remove it before running the evaluation again."
            )

        baseline_run = experiment.runs[-1] if experiment.runs else None
        current_run = Run(
            date=Date.today(),
            baseline_date=baseline_run.date if baseline_run else None,
            evaluations={},
        )
        experiment.runs.append(current_run)

        for pdf_file_path, document_context in loaded_pdfs:
            section_tree_actual = build_section_tree(document_context.soup)
            section_tree_ground_truth = load_json(
                ground_truth_dir / f"{pdf_file_path.stem}.json", SectionTree
            )
            evaluation = compute_evaluation(
                pdf_file_path.name,
                section_tree_actual,
                section_tree_ground_truth,
                baseline_run,
            )
            current_run.evaluations[pdf_file_path.name] = evaluation

        # ----- Generate evaluation summary
        total = len(current_run.evaluations)
        avg_score = sum(e.similarity for e in current_run.evaluations.values()) / total
        _LOGGER.info(f"\nEvaluation: {total} files, avg={avg_score:.4f}")

        if baseline_run:
            regressions = [
                e for e in current_run.evaluations.values() if e.diff is not None and e.diff < 0
            ]
            improvements = [
                e for e in current_run.evaluations.values() if e.diff is not None and e.diff > 0
            ]
            _LOGGER.info(f"vs {baseline_run.date}: ↓{len(regressions)} ↑{len(improvements)}")

            if regressions:
                for e in sorted(regressions, key=lambda x: x.diff)[:3]:
                    _LOGGER.info(f"  ⚠ {e.file_name}: {e.diff:+.4f}")
            if improvements:
                for e in sorted(improvements, key=lambda x: x.diff, reverse=True)[:3]:
                    _LOGGER.info(f"  ✓ {e.file_name}: {e.diff:+.4f}")

        dump_json(output_path, experiment)
        _LOGGER.info(f"Experiment saved to: {output_path}")
