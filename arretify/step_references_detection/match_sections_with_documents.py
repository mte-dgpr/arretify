from typing import List, Iterable

from bs4 import Tag

from arretify.types import PageElementOrString, ParsingContext
from arretify.utils.element_ranges import (
    iter_collapsed_range_right,
)
from arretify.utils.html import (
    make_css_class,
    assign_element_id,
    get_group_id,
    is_tag_and_matches,
)
from arretify.html_schemas import (
    SECTION_REFERENCE_SCHEMA,
    DOCUMENT_REFERENCE_SCHEMA,
)
from arretify.regex_utils import regex_tree

SECTION_REFERENCE_CSS_CLASS = make_css_class(SECTION_REFERENCE_SCHEMA)
DOCUMENT_REFERENCE_CSS_CLASS = make_css_class(DOCUMENT_REFERENCE_SCHEMA)


CONNECTOR_SECTION_TO_PARENT_NODE = regex_tree.Group(
    regex_tree.Sequence(
        [
            # Allows a maximum of 3 random words before the connector
            r"^(\s*[^\.\s]+){0,3}\s*",
            regex_tree.Branching(
                [
                    r"du",
                    r"de\s+l\'",
                    r"de\s+la",
                    r"des",
                ]
            ),
            r"\s*$",
        ]
    ),
    group_name="__connector_section_to_parent",
)


def match_sections_to_parents(
    parsing_context: ParsingContext,
    children: Iterable[PageElementOrString],
) -> List[PageElementOrString]:
    parsing_context.soup
    children = list(children)
    section_references = [
        tag
        for tag in children
        if is_tag_and_matches(tag, css_classes_in=[SECTION_REFERENCE_CSS_CLASS])
    ]

    for section_reference_tag in section_references:
        parent_reference_tag = _search_parent_reference_tag(section_reference_tag)
        if parent_reference_tag is None:
            continue

        group_id = get_group_id(section_reference_tag)
        if group_id is not None:
            section_references_in_group = [
                tag for tag in section_references if get_group_id(tag) == group_id
            ]
        else:
            section_references_in_group = [section_reference_tag]

        for section_reference_tag in section_references_in_group:
            document_element_id = assign_element_id(parent_reference_tag)
            section_reference_tag["data-parent_reference"] = document_element_id

    return children


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


def _search_parent_reference_tag(
    section_reference_tag: Tag,
) -> Tag | None:
    """
    For a given section reference tag, this function searches for its parent reference tag,
    by looking for connector words in between.

    For example, with :

        <a
            class="dsr-section_reference"
        >
            l'article 5
        </a>
        du
        <a
            class="dsr-section_reference"
        >
            présent arrêté
        </a>

    And given `<article 5>` as parameter, this function will return `<présent arrêté>`.
    """
    for element_range in iter_collapsed_range_right(section_reference_tag):
        # Make sure all elements in the range are contiguous.
        if element_range[-1].parent != section_reference_tag.parent:
            return None

        # Grow the range until we get 3 elements :
        # <reference tag> <connector string> <parent reference tag>
        if len(element_range) == 3:
            parent_reference_tag = element_range[2]
            if not is_tag_and_matches(
                parent_reference_tag,
                css_classes_in=[DOCUMENT_REFERENCE_CSS_CLASS, SECTION_REFERENCE_CSS_CLASS],
            ):
                return None

            connector_str = element_range[1]
            if not isinstance(connector_str, str) or not bool(
                regex_tree.match(CONNECTOR_SECTION_TO_PARENT_NODE, connector_str)
            ):
                return None

            return parent_reference_tag

        elif len(element_range) < 3:
            continue

        else:
            raise RuntimeError("Found more than 3 elements in the range, which is not expected")
    return None
