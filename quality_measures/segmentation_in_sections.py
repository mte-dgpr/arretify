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
from dotenv import load_dotenv
from pydantic import BaseModel

from arretify.law_data.apis.mistral import initialize_mistral_client
from arretify.pipeline import load_ocr_pages, load_pdf_file, run_pipeline
from arretify.semantic_tag_specs import AppendixSpec, MainSpec, SectionData, SectionSpec
from arretify.settings import Settings
from arretify.step_ocr import step_ocr
from arretify.step_segmentation import step_segmentation
from arretify.types import DocumentContext, ProtectedSoup, ProtectedTag, SessionContext
from arretify.utils.html_semantic import get_semantic_tag_data, is_semantic_tag

_LOGGER = logging.getLogger(Path(__file__).stem)


# -------------------- Data Models -------------------- #


class SectionTree(BaseModel):
    data: SectionData
    children: list["SectionTree"]


class Document(BaseModel):
    main: list[SectionTree]
    appendix: list[SectionTree] | None
    baseline: float | None = None
    """
    Baseline score for quality measurement.
    """


def dump_document(output_json_path: Path, document: Document) -> None:
    output_json_path.write_text(document.model_dump_json(indent=2), encoding="utf-8")


def load_document(json_path: Path) -> Document:
    return Document.model_validate_json(json_path.read_text(encoding="utf-8"))


# -------------------- Section Tree Building -------------------- #


def build_section_tree(soup: ProtectedSoup) -> Document:
    main_tag: ProtectedTag | None = None
    appendix_tag: ProtectedTag | None = None
    for child in soup.body.contents:
        if is_semantic_tag(child, spec_in=[MainSpec]):
            main_tag = child
        elif is_semantic_tag(child, spec_in=[AppendixSpec]):
            appendix_tag = child
    if main_tag is None:
        raise ValueError(f"'{MainSpec.tag_name}' semantic tag was not found.")

    main: list[SectionTree] = [
        _build_section_subtree(child)
        for child in main_tag.contents
        if is_semantic_tag(child, spec_in=[SectionSpec])
    ]

    appendix: list[SectionTree] | None = None
    if appendix_tag is not None:
        appendix = [
            _build_section_subtree(child)
            for child in appendix_tag.contents
            if is_semantic_tag(child, spec_in=[SectionSpec])
        ]

    return Document(main=main, appendix=appendix)


def _build_section_subtree(section_tag: ProtectedTag) -> SectionTree:
    children: list[SectionTree] = []
    for child in section_tag.contents:
        if is_semantic_tag(child, spec_in=[SectionSpec]):
            children.append(_build_section_subtree(child))
    return SectionTree(
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


def _generate_string_for_section_tree(children: list[SectionTree]) -> str:
    result = ""
    for child in children:
        result += f"{child.data.number}\n"
        result += _generate_string_for_section_tree(child.children)
    return result


def compute_similarity(children1: list[SectionTree], children2: list[SectionTree]) -> float:
    return Levenshtein.ratio(
        _normalize_section_tree_string(_generate_string_for_section_tree(children1)),
        _normalize_section_tree_string(_generate_string_for_section_tree(children2)),
    )


# -------------------- PDF Processing -------------------- #


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
            [step_segmentation],
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
            [step_ocr_with_cache, step_segmentation],
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

    subparsers = parser.add_subparsers(dest="action", required=True, help="Action to perform")

    generate_sections_parser = subparsers.add_parser(
        "generate_references",
        parents=[parent_parser],
        help="Generate section trees from HTML files",
    )
    generate_sections_parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="Output path.",
    )

    measure_quality_parser = subparsers.add_parser(
        "measure_quality",
        parents=[parent_parser],
        help="Measure quality between reference and generated sections",
    )
    measure_quality_parser.add_argument(
        "--reference",
        required=True,
        help="Path to the directory containing reference section tree JSON files.",
    )
    measure_quality_parser.add_argument(
        "--save-baseline",
        default=False,
        action="store_true",
        help="Take the scores as new baselines for future quality measurement.",
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

    loaded_documents = load_all_pdfs(input_dir, cache_dir=cache_dir)

    # ----- Performing the requested action
    if args.action == "generate_references":
        output_path = Path(args.output)
        output_path.mkdir(parents=True, exist_ok=True)
        _LOGGER.info(f"Output path: {output_path}")
        for pdf_file_path, document_context in loaded_documents:
            document = build_section_tree(document_context.soup)
            output_json_path = output_path / f"{pdf_file_path.stem}.json"
            dump_document(output_json_path, document)
            _LOGGER.info(f"Reference saved to: {output_json_path}")

    elif args.action == "measure_quality":
        reference_dir = Path(args.reference)
        if not reference_dir.is_dir():
            parser.error("Reference path must be a directory.")
        save_baseline = args.save_baseline
        if save_baseline:
            _LOGGER.info("Saving new baselines.")

        for pdf_file_path, document_context in loaded_documents:
            document_actual = build_section_tree(document_context.soup)
            reference_json_path = reference_dir / f"{pdf_file_path.stem}.json"
            document_reference = load_document(reference_json_path)
            similarity = compute_similarity(document_actual.main, document_reference.main)

            if save_baseline:
                document_reference.baseline = similarity
                dump_document(reference_json_path, document_reference)

            else:
                if document_reference.baseline:
                    diff = similarity - document_reference.baseline
                    if diff < 0:
                        _LOGGER.warning(
                            f"Quality regression detected for {pdf_file_path.name}: "
                            f"similarity {similarity:.4f} "
                            f"< baseline {document_reference.baseline:.4f} "
                            f"(diff {diff:.4f})"
                        )
                    else:
                        _LOGGER.info(
                            f"Quality check passed for {pdf_file_path.name}: "
                            f"similarity {similarity:.4f} "
                            f">= baseline {document_reference.baseline:.4f} "
                            f"(diff +{diff:.4f})"
                        )
                else:
                    _LOGGER.info(
                        f"No baseline available for {pdf_file_path.name}: "
                        f"similarity is {similarity:.4f}"
                    )
