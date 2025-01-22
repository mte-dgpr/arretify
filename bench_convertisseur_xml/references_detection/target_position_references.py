import re
from dataclasses import dataclass
from datetime import date
from bs4 import Tag, BeautifulSoup
from typing import Iterable, TypedDict, Tuple, cast, Pattern, Dict, Iterable, List

from ..settings import APP_ROOT, LOGGER
from bench_convertisseur_xml.utils.split import map_string_children, split_string_with_regex, reduce_children, map_match_flow, merge_strings
from bench_convertisseur_xml.html_schemas import TARGET_POSITION_REFERENCE_SCHEMA
from bench_convertisseur_xml.utils.html import make_data_tag, PageElementOrString
from bench_convertisseur_xml.utils.regex import join_with_or, named_groups_indices, without_named_groups
from bench_convertisseur_xml.parsing_misc.patterns import ET_VIRGULE_PATTERN_S, EME_PATTERN_S, ORDINAL_PATTERN_S, APOSTROPHE_PATTERN_S, ordinal_str_to_int

# TODO : 
# - Phrase and word index 

ARTICLE_NUM_PATTERN_S = r'\d+(\.(\d+|[a-zA-Z]+))*\.?'
# REF : https://reflex.sne.fr/codes-officiels
CODE_ARTICLE_NUM_PATTERN_S = r'(L|R|D)\.?\s*(\d+\s*-?\s*)*\d+'

# Order of patterns matters, from most specific to less specific.
ARTICLE_NUM_PATTERN_S_LIST = [
    f'(?P<code_article1>{CODE_ARTICLE_NUM_PATTERN_S})',
    f'(?P<article_ordinal1>{ORDINAL_PATTERN_S})',
    f'(?P<article_num1>{ARTICLE_NUM_PATTERN_S}){EME_PATTERN_S}?',
]

ARTICLE_RANGE_PATTERN_S = f'({join_with_or(ARTICLE_NUM_PATTERN_S_LIST)}) à (l{APOSTROPHE_PATTERN_S}article )?({join_with_or(named_groups_indices(ARTICLE_NUM_PATTERN_S_LIST, 2))})'

ARTICLE_PATTERN_S = f'articles? ({join_with_or(ARTICLE_NUM_PATTERN_S_LIST)})'

# Order of patterns matters, from most specific to less specific.
ARTICLE_PLURAL_PATTERN_S_LIST = [ARTICLE_RANGE_PATTERN_S] + ARTICLE_NUM_PATTERN_S_LIST
ARTICLE_PLURAL_PATTERN_LIST = [re.compile(pattern_s, re.IGNORECASE) for pattern_s in ARTICLE_PLURAL_PATTERN_S_LIST]
ARTICLE_PLURAL_PATTERN = re.compile(
    f'articles? (({join_with_or(without_named_groups(ARTICLE_PLURAL_PATTERN_S_LIST))}){ET_VIRGULE_PATTERN_S}?)+{ET_VIRGULE_PATTERN_S}({join_with_or(without_named_groups(ARTICLE_PLURAL_PATTERN_S_LIST))})',
    re.IGNORECASE
)


ALINEA_NUM_BEFORE_PATTERN_S = f'((?P<alinea_num>\d+){EME_PATTERN_S}?|(?P<alinea_ordinal>{ORDINAL_PATTERN_S})) alin[ée]a'
ALINEA_NUM_AFTER_PATTERN_S = f'alin[ée]a ((?P<alinea_num>\d+){EME_PATTERN_S}?|(?P<alinea_ordinal>{ORDINAL_PATTERN_S}))'
ALINEA_SYMBOL_PATTERN_S = f'(?P<alinea_num>\d+)°'

TARGET_POSITION_ALINEA_AND_ARTICLE_PATTERN_1 = re.compile(
    f'{ALINEA_NUM_BEFORE_PATTERN_S} (de l{APOSTROPHE_PATTERN_S})?{ARTICLE_PATTERN_S}', re.IGNORECASE)
TARGET_POSITION_ALINEA_AND_ARTICLE_PATTERN_2 = re.compile(
    f'{ALINEA_NUM_AFTER_PATTERN_S} (de l{APOSTROPHE_PATTERN_S})?{ARTICLE_PATTERN_S}', re.IGNORECASE)
TARGET_POSITION_ALINEA_AND_ARTICLE_PATTERN_3 = re.compile(
    f'{ALINEA_SYMBOL_PATTERN_S} (de l{APOSTROPHE_PATTERN_S})?{ARTICLE_PATTERN_S}', re.IGNORECASE)

TARGET_POSITION_ARTICLE_PATTERN = re.compile(f'{ARTICLE_PATTERN_S}', re.IGNORECASE)
TARGET_POSITION_ARTICLE_RANGE_PATTERN = re.compile(f'articles? {ARTICLE_RANGE_PATTERN_S}', re.IGNORECASE)

# Order of patterns matters, from most specific to less specific.
TARGET_POSITION_PATTERN_LIST = [
    TARGET_POSITION_ALINEA_AND_ARTICLE_PATTERN_1, 
    TARGET_POSITION_ALINEA_AND_ARTICLE_PATTERN_2,
    TARGET_POSITION_ALINEA_AND_ARTICLE_PATTERN_3,
    TARGET_POSITION_ARTICLE_RANGE_PATTERN,
    TARGET_POSITION_ARTICLE_PATTERN,
]


class ArticleMatchDict(TypedDict):
    article_num1: str | None
    article_ordinal1: str | None
    article_num2: str | None
    article_ordinal2: str | None


class AlineaMatchDict(TypedDict):
    alinea_num: str | None
    alinea_ordinal: str | None


class TargetPositionMatchDict(ArticleMatchDict, AlineaMatchDict):
    pass


def _handle_article_range_match_groupdict(match_dict: TargetPositionMatchDict) -> Dict:
    article_num1 = match_dict.get('article_num1')
    article_ordinal1 = match_dict.get('article_ordinal1')
    code_article1 = match_dict.get('code_article1')

    article_num2 = match_dict.get('article_num2')
    article_ordinal2 = match_dict.get('article_ordinal2')
    code_article2 = match_dict.get('code_article2')

    start = article_num1 or code_article1
    if article_ordinal1:
        start = ordinal_str_to_int(article_ordinal1)
    if not start:
        raise RuntimeError('No article number found')

    end = article_num2 or code_article2
    if article_ordinal2:
        end = ordinal_str_to_int(article_ordinal2)
    
    return dict(article_start=start, article_end=end)


def _handle_alinea_match_groupdict(match_dict: AlineaMatchDict) -> Dict:
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


def _parse_target_position_references(
    soup: BeautifulSoup,
    string: str,
    target_position_pattern: Pattern,
) -> Iterable[PageElementOrString]:
    def _render_match(soup, match: re.Match):
        target_position_data = dict()
        match_dict = cast(TargetPositionMatchDict, match.groupdict())
        target_position_data.update(_handle_article_range_match_groupdict(match_dict))
        target_position_data.update(_handle_alinea_match_groupdict(match_dict))
        yield make_data_tag(
            soup,
            TARGET_POSITION_REFERENCE_SCHEMA, 
            data=target_position_data,
            contents=[match.group(0)],
        )

    return map_match_flow(
        split_string_with_regex(string, target_position_pattern),
        lambda match: _render_match(soup, match),
    )
            

def _parse_plural_target_position_references(
    soup: BeautifulSoup,
    children: Iterable[PageElementOrString],
) -> Iterable[PageElementOrString]:
    def _render_plural_match(match: re.Match):
        new_children = reduce_children(
            [match.group(0)],
            ARTICLE_PLURAL_PATTERN_LIST,
            lambda children, pattern: map_string_children(
                children, 
                lambda string: _parse_target_position_references(soup, string, pattern)
            )
        )

        # If there's a string at the beginning of the match that doesn't correspond
        # with any reference e.g. "articles 1, 2", then add it to the first tag (<a>articles 1</a>, <a>2</a>), 
        # so that the matched text (e.g. "articles") is marked as handled and not detected
        # later by a new parsing operation.
        new_children = list(merge_strings(new_children))
        if isinstance(new_children[0], str):
            first_tag = new_children[1]
            assert isinstance(first_tag, Tag)
            first_tag.insert(0, new_children[0])
            new_children = new_children[1:]

        return new_children

    # For plural target positions, we need to first detect the whole
    # expression, with a list of articles, then single out each reference with a list of patterns.
    return map_string_children(
        children,
        lambda string: map_match_flow(
            split_string_with_regex(string, ARTICLE_PLURAL_PATTERN),
            _render_plural_match,
        )
    )


def parse_target_position_references(
    soup: BeautifulSoup,
    children: Iterable[PageElementOrString],
) -> List[PageElementOrString]:
    # First check for plural, cause it is the most exhaustive pattern
    new_children = list(_parse_plural_target_position_references(soup, children))
    return reduce_children(
        new_children,
        TARGET_POSITION_PATTERN_LIST, 
        lambda children, pattern: map_string_children(
            children, 
            lambda string: _parse_target_position_references(soup, string, pattern)
        ),
    )