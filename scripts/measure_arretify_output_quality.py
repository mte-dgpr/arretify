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
import json
import logging
from dataclasses import dataclass
from optparse import OptionParser
from pathlib import Path

from arretify.pipeline import load_html_file
from arretify.semantic_tag_specs import AppendixSpec, MainSpec, SectionData, SectionSpec
from arretify.settings import Settings
from arretify.types import ProtectedSoup, ProtectedTag, SessionContext
from arretify.utils.html_semantic import get_semantic_tag_data, is_semantic_tag

_LOGGER = logging.getLogger(Path(__file__).stem)


@dataclass(frozen=True)
class SectionTree:
    data: SectionData
    children: list["SectionTree"]


def build_section_tree(soup: ProtectedSoup) -> tuple[list[SectionTree], list[SectionTree] | None]:
    main_tag: ProtectedTag | None = None
    appendix_tag: ProtectedTag | None = None
    for child in soup.body.contents:
        if is_semantic_tag(child, spec_in=[MainSpec]):
            main_tag = child
        elif is_semantic_tag(child, spec_in=[AppendixSpec]):
            appendix_tag = child
    if main_tag is None:
        raise ValueError(f"'{MainSpec.tag_name}' semantic tag was not found.")

    main_sections = [
        _build_section_subtree(child)
        for child in main_tag.contents
        if is_semantic_tag(child, spec_in=[SectionSpec])
    ]
    if len(main_sections) == 0:
        raise ValueError(f"No sections found under '{MainSpec.tag_name}' semantic tag.")

    appendix_sections = None
    if appendix_tag is not None:
        appendix_sections = [
            _build_section_subtree(child)
            for child in appendix_tag.contents
            if is_semantic_tag(child, spec_in=[SectionSpec])
        ]
        if len(appendix_sections) == 0:
            raise ValueError(f"No sections found under '{AppendixSpec.tag_name}' semantic tag.")

    return main_sections, appendix_sections


def _build_section_subtree(section_tag: ProtectedTag) -> SectionTree:
    children: list[SectionTree] = []
    for child in section_tag.contents:
        if is_semantic_tag(child, spec_in=[SectionSpec]):
            children.append(_build_section_subtree(child))
    return SectionTree(
        data=get_semantic_tag_data(SectionSpec, section_tag),
        children=children,
    )


def _section_tree_to_dict(section_tree: SectionTree) -> dict:
    return dict(
        data=dict(
            number=section_tree.data.number,
            title=section_tree.data.title,
            type=section_tree.data.type,
        ),
        children=[_section_tree_to_dict(child) for child in section_tree.children],
    )


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
    )

    parser = OptionParser()
    parser.add_option(
        "-i",
        "--input",
        help="Input folder or single file path.",
    )
    parser.add_option(
        "-o",
        "--output",
        help="Output folder path.",
    )

    (options, args) = parser.parse_args()

    if not options.input:
        parser.error("Input file or folder path is required.")
    input_path = Path(options.input)
    if not input_path.is_dir():
        parser.error("Input path must be a directory.")

    if not options.output:
        parser.error("Output folder path is required.")
    output_path = Path(options.output)
    output_path.mkdir(parents=True, exist_ok=True)
    _LOGGER.info(f"Output will be saved to: {output_path}")

    session_context = SessionContext(
        settings=Settings.from_env(),
    )

    for html_file_path in sorted(input_path.iterdir()):
        if html_file_path.suffix != ".html":
            continue
        _LOGGER.info(f"Processing file: {html_file_path}")
        document_context = load_html_file(session_context, html_file_path)
        main_sections, appendix_sections = build_section_tree(document_context.soup)
        output_json_path = output_path / f"{html_file_path.stem}_sections.json"
        with output_json_path.open("w", encoding="utf-8") as f:
            json.dump(
                dict(
                    main=[_section_tree_to_dict(s) for s in main_sections],
                    appendix=(
                        [_section_tree_to_dict(s) for s in appendix_sections]
                        if appendix_sections
                        else None
                    ),
                ),
                f,
                ensure_ascii=False,
                indent=2,
            )
        _LOGGER.info(f"Section tree saved to: {output_json_path}")
    _LOGGER.info("Processing completed.")
