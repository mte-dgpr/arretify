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
from bs4 import Tag, BeautifulSoup
from typing import (
    Iterable,
    List,
    Iterator,
)

from arretify.types import (
    ElementGroupId,
    DocumentContext,
    SectionType,
)
from arretify.utils.functional import flat_map_string
from arretify.html_schemas import (
    SECTION_REFERENCE_SCHEMA,
)
from arretify.utils.html import (
    make_data_tag,
    make_group_id,
    assign_group_id,
    PageElementOrString,
    render_bool_attribute,
)
from arretify.parsing_utils.patterns import (
    ET_VIRGULE_PATTERN_S,
)
from arretify.parsing_utils.numbering import (
    EME_PATTERN_S,
    ORDINAL_PATTERN_S,
    ordinal_str_to_int,
)
from arretify.regex_utils import (
    regex_tree,
    map_regex_tree_match,
    flat_map_regex_tree_match,
    split_string_with_regex_tree,
    iter_regex_tree_match_strings,
    filter_regex_tree_match_children,
    repeated_with_separator,
    named_group,
)
from arretify.law_data.types import (
    Section,
    Document,
    DocumentType,
)
from arretify.law_data.uri import (
    render_uri,
    is_resolvable,
)

# TODO :
# - Phrase and word index

SectionNumber = str


def parse_section_references(
    document_context: DocumentContext,
    children: Iterable[PageElementOrString],
) -> List[PageElementOrString]:
    # First check for multiple, cause it is the most exhaustive pattern
    new_children = list(_parse_section_reference_multiple(document_context.soup, children))
    return list(_parse_section_references(document_context.soup, new_children))


# -------------------- Shared -------------------- #
# Remember that for Branching, order of patterns matters,
# from most specific to less specific.

# Articles from French law codes such as Code de l'environnement, etc.
# Examples : "L. 123-4", "R. 123-4", "D. 123-4"
# REF : https://reflex.sne.fr/codes-officiels
ARTICLE_NUMBER_FROM_CODE_NODE = regex_tree.Literal(
    r"(L|R|D)\.?\s*(\d+\s*-\s*)*\d+", key="article_number_from_code"
)

ORDINAL_NUMBER_NODE = regex_tree.Literal(ORDINAL_PATTERN_S, key="ordinal_number")

DOTTED_NUMBER_NODE = regex_tree.Sequence(
    [
        regex_tree.Literal(
            repeated_with_separator(
                r"\d+|[a-zA-Z]+",
                separator=r"\.",
                quantifier=(2, ...),
            ),
            key="dotted_number",
        ),
        # Sometimes there's an added dot at the end.
        r"\.?",
    ]
)

SIMPLE_NUMBER_NODE = regex_tree.Literal(
    named_group(r"\d+", "simple_number") + EME_PATTERN_S + r"?",
)

ARTICLE_NUMBER_NODE = regex_tree.Group(
    regex_tree.Branching(
        [
            ARTICLE_NUMBER_FROM_CODE_NODE,
            DOTTED_NUMBER_NODE,
            ORDINAL_NUMBER_NODE,
            SIMPLE_NUMBER_NODE,
        ]
    ),
    group_name="__article_number",
)


# Case when an article is ambiguously referred to with another
# word than "article", such as "paragraphe" or "point".
#
# Examples :
# - "paragraphe 1.23", only if in the form X.Y.Z
# - "paragraphe L.123-4"
ARTICLE_WRONGLY_CALLED_NUMBER_NODE = regex_tree.Group(
    regex_tree.Branching(
        [
            ARTICLE_NUMBER_FROM_CODE_NODE,
            DOTTED_NUMBER_NODE,
        ]
    ),
    group_name="__article_number",
)


ALINEA_NUMBER_NODE = regex_tree.Group(
    regex_tree.Branching(
        [
            ORDINAL_NUMBER_NODE,
            SIMPLE_NUMBER_NODE,
        ]
    ),
    group_name="__alinea_number",
)


UNKNOWN_SECTION_NUMBER_NODE = regex_tree.Group(
    regex_tree.Branching(
        [
            ORDINAL_NUMBER_NODE,
            SIMPLE_NUMBER_NODE,
        ]
    ),
    group_name="__unknown_section_number",
)


ARTICLE_RANGE_NODE = regex_tree.Sequence(
    [
        ARTICLE_NUMBER_NODE,
        r" à (l\'article )?",
        ARTICLE_NUMBER_NODE,
    ]
)


def _extract_section_number(match: regex_tree.Match) -> SectionNumber:
    article_number_from_code = match.match_dict.get("article_number_from_code")
    if article_number_from_code:
        return article_number_from_code.replace(" ", "").replace(".", "")

    dotted_number_from_code = match.match_dict.get("dotted_number")
    if dotted_number_from_code:
        return dotted_number_from_code

    ordinal_number = match.match_dict.get("ordinal_number")
    if ordinal_number:
        return str(ordinal_str_to_int(ordinal_number))

    simple_number = match.match_dict.get("simple_number")
    if simple_number:
        return simple_number

    raise RuntimeError("No section number found")


def _extract_section(
    section_reference_match: regex_tree.Match,
) -> Section:
    article_matches = filter_regex_tree_match_children(
        section_reference_match, ["__article_number"]
    )
    alinea_matches = filter_regex_tree_match_children(section_reference_match, ["__alinea_number"])
    unknown_section_matches = filter_regex_tree_match_children(
        section_reference_match, ["__unknown_section_number"]
    )

    if (
        sum(
            [
                bool(matches)
                for matches in [article_matches, alinea_matches, unknown_section_matches]
            ]
        )
        > 1
    ):
        raise RuntimeError("Several types of sections found in the same match")

    if len(article_matches) in [1, 2]:
        section_matches = article_matches
        section_type = SectionType.ARTICLE
    elif len(alinea_matches) in [1, 2]:
        section_matches = alinea_matches
        section_type = SectionType.ALINEA
    elif len(unknown_section_matches) in [1, 2]:
        section_matches = unknown_section_matches
        section_type = SectionType.UNKNOWN
    else:
        raise RuntimeError(
            f"Invalid number of matches : {len(article_matches)}, {len(alinea_matches)}"
        )

    section_start: SectionNumber | None = _extract_section_number(section_matches[0])
    section_end: SectionNumber | None = None
    if len(section_matches) == 2:
        section_end = _extract_section_number(section_matches[1])

    return Section(
        type=section_type,
        start_num=section_start,
        end_num=section_end,
    )


def _render_section_reference(
    soup: BeautifulSoup,
    section_reference_match: regex_tree.Match,
    group_id: ElementGroupId | None = None,
) -> Tag:
    document = Document(
        type=DocumentType.unknown,
    )
    section = _extract_section(section_reference_match)
    section_tag = make_data_tag(
        soup,
        SECTION_REFERENCE_SCHEMA,
        data=dict(
            uri=render_uri(document, section),
            is_resolvable=render_bool_attribute(is_resolvable(document, section)),
            parent_reference=None,
        ),
        contents=iter_regex_tree_match_strings(section_reference_match),
    )
    if group_id is not None:
        assign_group_id(section_tag, group_id)
    return section_tag


def _render_section_reference_multiple(
    soup: BeautifulSoup,
    section_reference_multiple_match: regex_tree.Match,
) -> Iterator[PageElementOrString]:
    group_id = make_group_id()
    return map_regex_tree_match(
        section_reference_multiple_match.children,
        lambda section_reference_match: _render_section_reference(
            soup,
            section_reference_match,
            group_id=group_id,
        ),
        allowed_group_names=["__section_reference"],
    )


# -------------------- Single section or section range -------------------- #
# Order of patterns matters, from most specific to less specific.
SECTION_REFERENCE_NODE = regex_tree.Group(
    regex_tree.Branching(
        [
            # -------- Articles -------- #
            # Example "article 1 à l'article 3"
            regex_tree.Sequence(
                [
                    r"articles? ",
                    ARTICLE_RANGE_NODE,
                ]
            ),
            # Example "article 3"
            regex_tree.Sequence(
                [
                    r"articles? ",
                    ARTICLE_NUMBER_NODE,
                ]
            ),
            # Examples :
            # - "paragraphe 1.23", only if in the form X.Y.Z
            # - "paragraphe L.123-4"
            regex_tree.Sequence(
                [
                    r"paragraphes? ",
                    ARTICLE_WRONGLY_CALLED_NUMBER_NODE,
                ]
            ),
            # -------- Alinéas -------- #
            # Examples :
            # - "alinéa 3"
            regex_tree.Sequence(
                [
                    regex_tree.Branching(
                        [
                            regex_tree.Sequence([ALINEA_NUMBER_NODE, r" (alinéa)"]),
                            regex_tree.Sequence([r"(alinéa) ", ALINEA_NUMBER_NODE]),
                        ]
                    ),
                ]
            ),
            # -------- Unknown sections -------- #
            # Examples :
            # - "paragraphe 3" -> can actually mean "alinéa 3" or in some cases "article 3"
            regex_tree.Sequence(
                [
                    regex_tree.Branching(
                        [
                            regex_tree.Sequence([UNKNOWN_SECTION_NUMBER_NODE, r" (paragraphe)"]),
                            regex_tree.Sequence([r"(paragraphe) ", UNKNOWN_SECTION_NUMBER_NODE]),
                        ]
                    ),
                ]
            ),
        ]
    ),
    group_name="__section_reference",
)


def _parse_section_references(
    soup: BeautifulSoup,
    children: Iterable[PageElementOrString],
) -> Iterable[PageElementOrString]:
    return flat_map_string(
        children,
        lambda string: map_regex_tree_match(
            split_string_with_regex_tree(SECTION_REFERENCE_NODE, string),
            lambda section_reference_match: _render_section_reference(
                soup,
                section_reference_match,
            ),
            allowed_group_names=["__section_reference"],
        ),
    )


# -------------------- Multiple sections -------------------- #
SECTION_REFERENCE_MULTIPLE_NODE = regex_tree.Group(
    regex_tree.Branching(
        [
            # Examples :
            # - "Les alinéas 3 et 4"
            # - "alinéa 3, alinéa 4 et 5"
            regex_tree.Sequence(
                [
                    # Positive lookahead so there's a match only
                    # if the strings starts with the word "alinéa".
                    r"(?=alinéas? )",
                    regex_tree.Repeat(
                        regex_tree.Group(
                            regex_tree.Sequence(
                                [
                                    r"(alinéas? )?",
                                    ALINEA_NUMBER_NODE,
                                ]
                            ),
                            group_name="__section_reference",
                        ),
                        separator=ET_VIRGULE_PATTERN_S,
                        quantifier=(2, ...),
                    ),
                ]
            ),
            # Examples :
            # - "Les articles 3 et 4"
            # - "Les articles 3, 4 et 5"
            # - "Les articles 3 à 6, 9 et 12 à 14"
            regex_tree.Sequence(
                [
                    # Positive lookahead so there's a match only
                    # if the strings starts with the word "article".
                    r"(?=articles? )",
                    regex_tree.Repeat(
                        regex_tree.Group(
                            regex_tree.Sequence(
                                [
                                    r"(articles? )?",
                                    regex_tree.Branching(
                                        [
                                            ARTICLE_RANGE_NODE,
                                            ARTICLE_NUMBER_NODE,
                                        ]
                                    ),
                                ]
                            ),
                            group_name="__section_reference",
                        ),
                        separator=ET_VIRGULE_PATTERN_S,
                        quantifier=(2, ...),
                    ),
                ]
            ),
            # Examples :
            # - "Les paragraphes 3 et 4"
            regex_tree.Sequence(
                [
                    # Positive lookahead so there's a match only
                    # if the strings starts with the word "paragraphe".
                    r"(?=paragraphes? )",
                    regex_tree.Repeat(
                        regex_tree.Group(
                            regex_tree.Sequence(
                                [
                                    r"(paragraphes? )?",
                                    UNKNOWN_SECTION_NUMBER_NODE,
                                ]
                            ),
                            group_name="__section_reference",
                        ),
                        separator=ET_VIRGULE_PATTERN_S,
                        quantifier=(2, ...),
                    ),
                ]
            ),
        ]
    ),
    group_name="__section_reference_multiple",
)


def _parse_section_reference_multiple(
    soup: BeautifulSoup,
    children: Iterable[PageElementOrString],
):
    # For multiple arretes, we need to first parse some of the attributes in common
    # before parsing each individual arrete reference.
    return flat_map_string(
        children,
        lambda string: flat_map_regex_tree_match(
            split_string_with_regex_tree(SECTION_REFERENCE_MULTIPLE_NODE, string),
            lambda section_reference_multiple_match: _render_section_reference_multiple(
                soup,
                section_reference_multiple_match,
            ),
            allowed_group_names=["__section_reference_multiple"],
        ),
    )
