import re
from dataclasses import dataclass
from datetime import date
from bs4 import Tag, BeautifulSoup
from typing import Iterable, TypedDict, Tuple, cast, Pattern, Dict, Iterable, List

from ..settings import APP_ROOT, LOGGER
from bench_convertisseur_xml.utils.functional import flat_map_non_string, flat_map_string
from bench_convertisseur_xml.html_schemas import TARGET_POSITION_REFERENCE_SCHEMA
from bench_convertisseur_xml.utils.html import make_data_tag, PageElementOrString
from bench_convertisseur_xml.parsing_misc.patterns import ET_VIRGULE_PATTERN_S, EME_PATTERN_S, ORDINAL_PATTERN_S, APOSTROPHE_PATTERN_S, ordinal_str_to_int
from bench_convertisseur_xml.regex_utils import regex_tree, flat_map_regex_tree_match, split_string_with_regex_tree, MatchDict, RegexTreeMatch

# TODO : 
# - Phrase and word index 


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
        r'((?P<alinea_num>\d+)' + EME_PATTERN_S + r'?|(?P<alinea_ordinal>' + ORDINAL_PATTERN_S + r')) alin[ée]a',
        r'alin[ée]a ((?P<alinea_num>\d+)' + EME_PATTERN_S + r'?|(?P<alinea_ordinal>' + ORDINAL_PATTERN_S + r'))',
        r'(?P<alinea_num>\d+)°',
    ]), 
    group_name='__alinea'
)


ARTICLE_RANGE_NODE = regex_tree.Sequence([
    ARTICLE_ID_NODE,
    r' à (l' + APOSTROPHE_PATTERN_S + r'article )?',
    ARTICLE_ID_NODE,
])


# Order of patterns matters, from most specific to less specific.
TARGET_POSITION_NODE = regex_tree.Group(
    regex_tree.Branching([
        regex_tree.Sequence([
            ALINEA_NODE,
            r' (de l' + APOSTROPHE_PATTERN_S + r')?articles? ',
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
    group_name='__target_position'
)


TARGET_POSITION_PLURAL_NODE = regex_tree.Group(
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
            group_name='__target_position'
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
                    group_name='__target_position'
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
            group_name='__target_position'
        ),
    ]), 
    group_name='__target_position_plural'
)


def _handle_article_match_dict(match_dict: MatchDict) -> Dict:
    article_num = match_dict.get('num')
    article_ordinal = match_dict.get('ordinal')
    article_code = match_dict.get('code')

    article_id = article_num or article_code
    if article_ordinal:
        article_id = ordinal_str_to_int(article_ordinal)
    return dict(article_id=article_id)


def _handle_alinea_match_dict(match_dict: MatchDict) -> Dict:
    alinea_num = match_dict.get('alinea_num')
    alinea_ordinal = match_dict.get('alinea_ordinal')

    if alinea_num and alinea_ordinal:
        raise RuntimeError('Both alinea_num and alinea_ordinal found')

    alinea_start = None
    if alinea_num:
        alinea_start = alinea_num
    elif alinea_ordinal:
        alinea_start = ordinal_str_to_int(alinea_ordinal)
    return dict(alinea_start=alinea_start, alinea_end=None)


def _render_target_position_group_match(soup, regex_tree_match: RegexTreeMatch) -> Tag:
    contents: List[PageElementOrString] = []
    alinea_dict: Dict | None = None
    article_start_dict: Dict | None = None
    article_end_dict: Dict | None = None

    for str_or_group in regex_tree_match.children:
        if isinstance(str_or_group, str):
            contents.append(str_or_group)
        
        elif str_or_group.group_name == '__article_id':
            contents.extend(str_or_group.string_children)
            if not article_start_dict:
                article_start_dict = _handle_article_match_dict(str_or_group.match_dict)
            elif not article_end_dict:
                article_end_dict = _handle_article_match_dict(str_or_group.match_dict)
            else:
                raise RuntimeError('Too many article matches')
        
        elif str_or_group.group_name == '__alinea':
            contents.extend(str_or_group.string_children)
            alinea_dict = _handle_alinea_match_dict(str_or_group.match_dict)
        
        else:
            raise RuntimeError(f'Unknown group {str_or_group.group_name}')
        
    if not article_start_dict:
        raise RuntimeError('No article found')
    
    return make_data_tag(
        soup,
        TARGET_POSITION_REFERENCE_SCHEMA, 
        data=dict(
            article_start=article_start_dict['article_id'],
            article_end=article_end_dict['article_id'] if article_end_dict else None,
            alinea_start=alinea_dict['alinea_start'] if alinea_dict else None,
            alinea_end=None,
        ),
        contents=contents,
    )


def _parse_target_position_references(
    soup: BeautifulSoup,
    children: Iterable[PageElementOrString],
) -> Iterable[PageElementOrString]:
    return flat_map_string(
        children,
        lambda string: flat_map_regex_tree_match(
            split_string_with_regex_tree(TARGET_POSITION_NODE, string),
            lambda target_position_group_match: [
                _render_target_position_group_match(
                    soup, 
                    target_position_group_match,
                ),
            ],
            allowed_group_names=['__target_position'],
        )
    )


def _parse_plural_target_position_references(
    soup: BeautifulSoup,
    children: Iterable[PageElementOrString],
):
    # For plural arretes, we need to first parse some of the attributes in common
    # before parsing each individual arrete reference.
    return flat_map_string(
        children,
        lambda string: flat_map_regex_tree_match(
            split_string_with_regex_tree(TARGET_POSITION_PLURAL_NODE, string),
            lambda target_position_plural_group_match: flat_map_regex_tree_match(
                target_position_plural_group_match.children,
                lambda target_position_group_match: [
                    _render_target_position_group_match(
                        soup, 
                        target_position_group_match,
                    ),
                ],
                allowed_group_names=['__target_position'],
            ),
            allowed_group_names=['__target_position_plural'],
        )
    )


def parse_target_position_references(
    soup: BeautifulSoup,
    children: Iterable[PageElementOrString],
) -> List[PageElementOrString]:
    # First check for plural, cause it is the most exhaustive pattern
    new_children = list(_parse_plural_target_position_references(soup, children))
    return list(_parse_target_position_references(soup, new_children))