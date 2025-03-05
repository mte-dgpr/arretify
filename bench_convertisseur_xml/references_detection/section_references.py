import re
from dataclasses import dataclass
from datetime import date
from bs4 import Tag, BeautifulSoup
from typing import Iterable, TypedDict, Tuple, cast, Pattern, Dict, Iterable, List, Union

from ..settings import APP_ROOT, LOGGER
from bench_convertisseur_xml.utils.functional import flat_map_string
from bench_convertisseur_xml.html_schemas import SECTION_REFERENCE_SCHEMA, SECTION_REFERENCE_MULTIPLE_SCHEMA
from bench_convertisseur_xml.utils.html import make_data_tag, PageElementOrString
from bench_convertisseur_xml.parsing_utils.patterns import ET_VIRGULE_PATTERN_S, EME_PATTERN_S, ORDINAL_PATTERN_S, ordinal_str_to_int
from bench_convertisseur_xml.regex_utils import regex_tree, flat_map_regex_tree_match, split_string_with_regex_tree, iter_regex_tree_match_strings, filter_regex_tree_match_children
from bench_convertisseur_xml.law_data.types import Section
from bench_convertisseur_xml.law_data.uri import render_uri
from bench_convertisseur_xml.types import URI

# TODO : 
# - Phrase and word index 

ArticleId = str
Alinea = int


def parse_section_references(
    soup: BeautifulSoup,
    children: Iterable[PageElementOrString],
) -> List[PageElementOrString]:
    # First check for multiple, cause it is the most exhaustive pattern
    new_children = list(_parse_section_reference_multiple_articles(soup, children))
    new_children = list(_parse_section_reference_multiple_alineas(soup, new_children))
    return list(_parse_section_references(soup, new_children))


# -------------------- Shared -------------------- #
# Order of patterns matters, from most specific to less specific.
ARTICLE_ID_NODE = regex_tree.Group(
    regex_tree.Branching([
        # REF : https://reflex.sne.fr/codes-officiels
        r'(?P<code>(L|R|D)\.?\s*(\d+\s*-?\s*)*\d+)',
        r'(?P<ordinal>' + ORDINAL_PATTERN_S + r')',
        r'(?P<num>\d+(\.(\d+|[a-zA-Z]+))*\.?)' + EME_PATTERN_S + r'?',
    ]), 
    group_name='__article_id'
)


ALINEA_NODE = regex_tree.Group(
    regex_tree.Branching([
        r'(?P<alinea_num>\d+)' + EME_PATTERN_S + r'?',
        r'(?P<alinea_ordinal>' + ORDINAL_PATTERN_S + r')',
    ]),
    group_name='__alinea'
)


ARTICLE_RANGE_NODE = regex_tree.Sequence([
    ARTICLE_ID_NODE,
    r' à (l\'article )?',
    ARTICLE_ID_NODE,
])


def _extract_article_id(match: regex_tree.Match) -> ArticleId:
    match_dict = match.match_dict
    article_num = match_dict.get('num')
    article_ordinal = match_dict.get('ordinal')
    article_code = match_dict.get('code')

    article_id = article_num or article_code
    if article_ordinal:
        article_id = str(ordinal_str_to_int(article_ordinal))

    if not article_id:
        raise RuntimeError('No article found')

    return article_id


def _extract_alinea(match: regex_tree.Match) -> Alinea:
    match_dict = match.match_dict
    alinea_num = match_dict.get('alinea_num')
    alinea_ordinal = match_dict.get('alinea_ordinal')

    if alinea_num and alinea_ordinal:
        raise RuntimeError('Both alinea_num and alinea_ordinal found')

    alinea: Union[Alinea, None] = None
    if alinea_num:
        alinea = int(alinea_num)
    elif alinea_ordinal:
        alinea = ordinal_str_to_int(alinea_ordinal)

    if alinea is None:
        raise RuntimeError('No alinea found')

    return alinea


def _extract_uri(
    article_tree_match: regex_tree.Match, 
    alinea_tree_match: regex_tree.Match | None = None,
) -> URI:
    article_matches = filter_regex_tree_match_children(article_tree_match, ['__article_id'])
    if alinea_tree_match:
        alinea_matches = filter_regex_tree_match_children(alinea_tree_match, ['__alinea'])
    else:
        alinea_matches = []
    
    if len(article_matches) not in [1, 2]:
        raise RuntimeError('Expected exactly one or two article matches')
    if len(alinea_matches) not in [0, 1, 2]:
        raise RuntimeError('Expected exactly zero, one or two alinea matches')

    alinea_start: Alinea | None = None
    alinea_end: Alinea | None = None
    if alinea_matches:
        alinea_start = _extract_alinea(alinea_matches[0])
    if len(alinea_matches) == 2:
        alinea_end = _extract_alinea(alinea_matches[1])

    article_start: ArticleId = _extract_article_id(article_matches[0])
    article_end: ArticleId | None = None
    if len(article_matches) == 2:
        article_end = _extract_article_id(article_matches[1])

    sections = [
        Section.article(
            article_start, 
            article_end,
        )
    ]

    if alinea_start:
        sections.append(
            Section.alinea(
                alinea_start,
                alinea_end,
            )
        )

    return render_uri(
        None,
        *sections,
    )


# -------------------- Single article (or range), single alinea -------------------- #
# Order of patterns matters, from most specific to less specific.
SECTION_REFERENCE_NODE = regex_tree.Group(
    regex_tree.Branching([
        regex_tree.Sequence([
            regex_tree.Branching([
                regex_tree.Sequence([ALINEA_NODE, r' (alinéa|paragraphe)']),
                regex_tree.Sequence([r'(alinéa|paragraphe) ', ALINEA_NODE]),
                regex_tree.Group(r'(?P<alinea_num>\d+)°', group_name='__alinea'),
            ]),
            r' (de l\')?articles? ',
            ARTICLE_ID_NODE,
        ]),
        
        regex_tree.Sequence([
            r'articles? ',
            ARTICLE_RANGE_NODE,
        ]),

        regex_tree.Sequence([
            r'articles? ',
            ARTICLE_ID_NODE,
        ]),
    ]), 
    group_name='__section_reference'
)


def _parse_section_references(
    soup: BeautifulSoup,
    children: Iterable[PageElementOrString],
) -> Iterable[PageElementOrString]:
    return flat_map_string(
        children,
        lambda string: flat_map_regex_tree_match(
            split_string_with_regex_tree(SECTION_REFERENCE_NODE, string),
            lambda section_reference_match: [
                make_data_tag(
                    soup,
                    SECTION_REFERENCE_SCHEMA, 
                    data=dict(uri=_extract_uri(
                        section_reference_match, 
                        section_reference_match
                    )),
                    contents=iter_regex_tree_match_strings(section_reference_match),
                ),
            ],
            allowed_group_names=['__section_reference'],
        )
    )


# -------------------- Multiple articles -------------------- #
# Example : "Les articles 3 et 4"
SECTION_REFERENCE_MULTIPLE_ARTICLES_NODE = regex_tree.Group(
    regex_tree.Sequence([
        regex_tree.Group(
            regex_tree.Sequence([
                r'articles? ',
                # Order of patterns matters, from most specific to less specific.
                regex_tree.Branching([
                    ARTICLE_RANGE_NODE, 
                    ARTICLE_ID_NODE,
                ]),
            ]), 
            group_name='__section_reference'
        ),

        ET_VIRGULE_PATTERN_S,
        
        regex_tree.Quantifier(
            regex_tree.Sequence([
                regex_tree.Group(
                    # Order of patterns matters, from most specific to less specific.
                    regex_tree.Branching([
                        ARTICLE_RANGE_NODE, 
                        ARTICLE_ID_NODE,
                    ]), 
                    group_name='__section_reference'
                ),
                ET_VIRGULE_PATTERN_S,
            ]),
            '*',
        ),
        
        # Order of patterns matters, from most specific to less specific.
        regex_tree.Group(
            regex_tree.Branching([
                ARTICLE_RANGE_NODE,
                ARTICLE_ID_NODE,
            ]),
            group_name='__section_reference'
        ),
    ]), 
    group_name='__section_reference_multiple'
)


def _parse_section_reference_multiple_articles(
    soup: BeautifulSoup,
    children: Iterable[PageElementOrString],
):
    # For multiple arretes, we need to first parse some of the attributes in common
    # before parsing each individual arrete reference.
    return flat_map_string(
        children,
        lambda string: flat_map_regex_tree_match(
            split_string_with_regex_tree(SECTION_REFERENCE_MULTIPLE_ARTICLES_NODE, string),
            lambda section_reference_multiple_match: [
                make_data_tag(
                    soup,
                    SECTION_REFERENCE_MULTIPLE_SCHEMA, 
                    contents=flat_map_regex_tree_match(
                        section_reference_multiple_match.children,
                        lambda section_reference_match: [
                            make_data_tag(
                                soup,
                                SECTION_REFERENCE_SCHEMA, 
                                data=dict(uri=_extract_uri(section_reference_match)),
                                contents=iter_regex_tree_match_strings(section_reference_match),
                            ),
                        ],
                        allowed_group_names=['__section_reference'],
                    ),
                )
            ],
            allowed_group_names=['__section_reference_multiple'],
        )
    )


# -------------------- Multiple alineas -------------------- #
# Example "Les paragraphes 3 et 4 de l'article 8.5.1.1"
SECTION_REFERENCE_MULTIPLE_ALINEA_NODE = regex_tree.Group(
    regex_tree.Sequence([
        regex_tree.Group(
            regex_tree.Sequence([
                r'(alinéas|paragraphes) ',
                ALINEA_NODE,
            ]),
            group_name='__section_reference',
        ),
        
        ET_VIRGULE_PATTERN_S,

        regex_tree.Quantifier(
            regex_tree.Sequence([
                regex_tree.Group(
                    ALINEA_NODE,
                    group_name='__section_reference',
                ),
                ET_VIRGULE_PATTERN_S,
            ]),
            quantifier='*'
        ),

        regex_tree.Group(
            regex_tree.Sequence([
                ALINEA_NODE,
                r' (de l\')?articles? ',
                ARTICLE_ID_NODE,
            ]),
            group_name='__section_reference_with_article'
        ),
    ]),
    group_name='__section_reference_multiple'
)


def _parse_section_reference_multiple_alineas(
    soup: BeautifulSoup,
    children: Iterable[PageElementOrString],
):
    # For multiple arretes, we need to first parse some of the attributes in common
    # before parsing each individual arrete reference.
    return flat_map_string(
        children,
        lambda string: flat_map_regex_tree_match(
            split_string_with_regex_tree(SECTION_REFERENCE_MULTIPLE_ALINEA_NODE, string),
            lambda section_reference_multiple_match: [
                make_data_tag(
                    soup,
                    SECTION_REFERENCE_MULTIPLE_SCHEMA, 
                    contents=flat_map_regex_tree_match(
                        section_reference_multiple_match.children,
                        lambda section_reference_match: [
                            make_data_tag(
                                soup,
                                SECTION_REFERENCE_SCHEMA, 
                                data=dict(
                                    uri=_extract_uri(
                                        # Find the tree match that contains the article id
                                        # and pass it to the uri extraction function
                                        filter_regex_tree_match_children(
                                            section_reference_multiple_match, 
                                            group_names=['__section_reference_with_article']
                                        )[0],
                                        section_reference_match,
                                    )
                                ),
                                contents=iter_regex_tree_match_strings(section_reference_match),
                            ),
                        ],
                        allowed_group_names=['__section_reference', '__section_reference_with_article'],
                    )
                )
            ],
            allowed_group_names=['__section_reference_multiple'],
        )
    )