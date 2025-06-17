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
from typing import List, Iterable, Tuple

from bs4 import Tag

from arretify.utils.html import is_tag_and_matches
from arretify.html_schemas import (
    DOCUMENT_REFERENCE_SCHEMA,
    SECTION_REFERENCE_SCHEMA,
)
from arretify.law_data.types import Document, Section


ReferenceTree = List[List[Tag]]
ReferenceTreeTraversal = Iterable[Tuple[Tag, Document | None, List[Section]]]


def build_and_traverse_reference_tree(
    section_reference_tag: Tag,
) -> ReferenceTreeTraversal:
    """
    Traverse the reference tree formed by a chain of connected
    sections and document references.

    For example :

    with "l'alinéa 1 et l'alinéa 2 de l'article 5 du présent arrêté"

    This function will yield :
    (<Tag: présent arrêté>, <Document: présent arrêté>, [])
    (<Tag: article 5>, <Document: présent arrêté>, [<Section: article 5>])
    (<Tag: alinéa 1>, <Document: présent arrêté>, [<Section: article 5>, <Section: alinéa 1>])
    (<Tag: alinéa 2>, <Document: présent arrêté>, [<Section: article 5>, <Section: alinéa 2>])
    """
    reference_tree = build_reference_tree(section_reference_tag)
    return traverse_reference_tree(reference_tree)


def build_reference_tree(
    section_reference_tag: Tag,
) -> ReferenceTree:
    """
    References appear in text as a chain of sub sections of a document,
    For example : "l'alinéa 1 et l'alinéa 2 de l'article 5 du présent arrêté".

    We parse each one of these sections individually and store them in a section
    reference tag, and then connect each section to its parent through the
    `data-parent_reference` attribute. For example :

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
            [<Tag: présent arrêté>, <Tag: article 5>, <Tag: alinéa 1>],
            [<Tag: présent arrêté>, <Tag: article 5>, <Tag: alinéa 2>],
        ]
    """
    assert section_reference_tag.parent is not None, "section_reference_tag has no parent"
    reference_tags = [
        tag
        for tag in section_reference_tag.parent.children
        if is_tag_and_matches(
            tag,
            css_classes_in=[
                DOCUMENT_REFERENCE_SCHEMA.css_class,
                SECTION_REFERENCE_SCHEMA.css_class,
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

    reference_tree: List[List[Tag]] = [[root_reference_tag]]
    should_continue = True
    while should_continue is True:
        should_continue = False
        new_reference_branches: List[List[Tag]] = []
        for branch in reference_tree:
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

        reference_tree = new_reference_branches

    return reference_tree


def traverse_reference_tree(
    reference_tree: ReferenceTree,
) -> ReferenceTreeTraversal:
    """
    Function allowing to traverse a reference tree (depth-first).
    """
    seen: List[Tag] = []
    for branch in reference_tree:
        document: Document | None = None
        sections: list[Section] = []
        for reference_tag in branch:
            if not is_tag_and_matches(
                reference_tag,
                css_classes_in=[
                    SECTION_REFERENCE_SCHEMA.css_class,
                    DOCUMENT_REFERENCE_SCHEMA.css_class,
                ],
            ):
                raise ValueError(f"Unexpected tag in reference branch: {reference_tag}")

            if is_tag_and_matches(
                reference_tag, css_classes_in=[SECTION_REFERENCE_SCHEMA.css_class]
            ):
                sections.append(Section.from_tag(reference_tag))
            elif is_tag_and_matches(
                reference_tag, css_classes_in=[DOCUMENT_REFERENCE_SCHEMA.css_class]
            ):
                document = Document.from_tag(reference_tag)

            # Avoid handling the same section multiple times
            if any([reference_tag is other_tag for other_tag in seen]):
                continue

            seen.append(reference_tag)
            # Send a copy of the sections list otherwise
            # it will be modified in the next iteration
            yield reference_tag, document, sections[:]
