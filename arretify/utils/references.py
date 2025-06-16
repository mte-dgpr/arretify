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
from typing import List, Iterator, Tuple

from bs4 import Tag

from arretify.utils.html import is_tag_and_matches, make_css_class
from arretify.html_schemas import (
    DOCUMENT_REFERENCE_SCHEMA,
    SECTION_REFERENCE_SCHEMA,
)
from arretify.law_data.types import Document, Section


DOCUMENT_REFERENCE_CSS_CLASS = make_css_class(DOCUMENT_REFERENCE_SCHEMA)
SECTION_REFERENCE_CSS_CLASS = make_css_class(SECTION_REFERENCE_SCHEMA)


def build_reference_tree(
    section_reference_tag: Tag,
) -> List[List[Tag]]:
    """
    References appear in text as a chain of sub sections of a document,
    For example : "l'alinéa 1 et l'alinéa 2 de l'article 5 du présent arrêté".

    We parse each one of these sections individually to a section reference tag, and then connect
    each section to its parent through the `data-parent_reference` attribute.
    For example :

        l'
        <a
            data-parent_reference="3"
        >
            alinéa 1
        </a>
        et
        <a
            data-parent_reference="3"
        >
            alinéa 2
        </a>
        de
        <a
            data-element_id="3"
            data-parent_reference="4"
        >
            l'article 5
        </a>
        du
        <a
            data-element_id="4"
        >
            présent arrêté
        </a>

    This function builds the tree of reference sections which `section_reference_tag` is part of.
    It returns a list of branches, where each branch is a list of tags.
    First element of the branch is the root (least specific reference, e.g. a document) and
    last element the leaf (most specific reference, e.g. an alinea).

    With the example above, this function would return the following:
        [
            [<présent arrêté>, <article 5>, <alinéa 1>],
            [<présent arrêté>, <article 5>, <alinéa 2>],
        ]
    """
    assert section_reference_tag.parent is not None, "section_reference_tag has no parent"
    reference_tags = [
        tag
        for tag in section_reference_tag.parent.children
        if is_tag_and_matches(
            tag,
            css_classes_in=[
                DOCUMENT_REFERENCE_CSS_CLASS,
                SECTION_REFERENCE_CSS_CLASS,
            ],
        )
    ]

    root_reference_tag = section_reference_tag
    while root_reference_tag.get("data-parent_reference", None) is not None:
        parent_reference_tag_matches = [
            tag
            for tag in reference_tags
            if tag.get("data-element_id", None) == root_reference_tag["data-parent_reference"]
        ]
        if len(parent_reference_tag_matches) != 1:
            raise RuntimeError("Found more than one parent reference tag, which is not expected")
        root_reference_tag = parent_reference_tag_matches[0]

    reference_branches: List[List[Tag]] = [[root_reference_tag]]
    should_continue = True
    while should_continue is True:
        should_continue = False
        new_reference_branches: List[List[Tag]] = []
        for branch in reference_branches:
            parent_reference_tag = branch[-1]
            # If the parent reference tag has no data-element_id,
            # it can't be referenced, so can't have children.
            if parent_reference_tag.get("data-element_id", None) is None:
                new_reference_branches.append(branch)
                continue

            children_reference_tags = [
                tag
                for tag in reference_tags
                if tag.get("data-parent_reference", None) == parent_reference_tag["data-element_id"]
            ]

            # if no children, we have reached a leaf.
            if len(children_reference_tags) == 0:
                new_reference_branches.append(branch)
                continue

            should_continue = True
            new_reference_branches.extend([[*branch, child] for child in children_reference_tags])

        reference_branches = new_reference_branches

    return reference_branches


def iter_section_references(
    document_reference_tag: Tag,
) -> Iterator[Tuple[Tag, Document, List[Section]]]:
    document = Document.from_tag(document_reference_tag)
    reference_branches = build_reference_tree(document_reference_tag)
    seen: List[Tag] = []
    for branch in reference_branches:
        sections: list[Section] = []
        for section_reference_tag in branch[1:]:
            if not is_tag_and_matches(
                section_reference_tag, css_classes_in=[SECTION_REFERENCE_CSS_CLASS]
            ):
                raise ValueError(f"Unexpected tag in reference branch: {section_reference_tag}")

            # Avoid handling the same section multiple times
            if any([section_reference_tag is other_tag for other_tag in seen]):
                sections.append(Section.from_tag(section_reference_tag))
                continue

            seen.append(section_reference_tag)
            sections.append(Section.from_tag(section_reference_tag))
            yield section_reference_tag, document, sections
