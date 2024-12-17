import re
from dataclasses import dataclass
from datetime import date
from bs4 import Tag, BeautifulSoup, NavigableString
from typing import Literal, List, get_args, cast, TypedDict, Pattern, Tuple, Iterator

from ..settings import APP_ROOT, LOGGER
from .dates import parse_date, DATE1_RES, DATE2_RES, DateMatchDict, handle_date_match_groupdict, make_date_element
from bench_convertisseur_xml.utils.text import normalize_text
from bench_convertisseur_xml.utils.html import PageElementOrString, make_element
from bench_convertisseur_xml.utils.regex import split_string_with_regex, split_string_from_match
from bench_convertisseur_xml.html_schemas import ARRETE_REFERENCE_SCHEMA


ARRETE_TYPES: List[str] = ['préfectoral', 'ministériel']

RefType = Literal['article']
Authority = Literal['préfectoral', 'ministériel']

# code1 : matches all codes starting with n°
# code2 : match all codes of type 12-77LY87-7878 or 1L/77/9998
CODE_RE = r'(([nN]° ?(?P<code1>\S+))|(?P<code2>\S+[/\-]\S+))(\s|$)'


class CodeMatchDict(TypedDict):
    code1: str
    code2: str


def parse_code(match_dict: CodeMatchDict):
    return match_dict.get('code1') or match_dict.get('code2')


ARRETE_BASE_RES = r'arrêté ((?P<authority>préfectoral|ministériel) (modifié )?)?((?P<qualifier>complémentaire|d\'autorisation|d\'autorisation initial|de mise en demeure|de mesures d\'urgence) )?'
ARRETE_FILLER_RES = r'(transmis a l\'exploitant par (courrier recommandé|courrier) )?((du|en date du) )?'

ARRETE_DATE1_RE = re.compile(
    f'{ARRETE_BASE_RES}{ARRETE_FILLER_RES}(?P<date>{DATE1_RES})'
)
ARRETE_DATE2_RE = re.compile(
    f'{ARRETE_BASE_RES}{ARRETE_FILLER_RES}(?P<date>{DATE2_RES})'
)
ARRETE_CODE_AND_DATE1_RE = re.compile(
    f'{ARRETE_BASE_RES}{CODE_RE}{ARRETE_FILLER_RES}(?P<date>{DATE1_RES})'
)
ARRETE_CODE_AND_DATE2_RE = re.compile(
    f'{ARRETE_BASE_RES}{CODE_RE}{ARRETE_FILLER_RES}(?P<date>{DATE2_RES})'
)
ARRETE_CODE_RE = re.compile(f'{ARRETE_BASE_RES}{CODE_RE}')

ARRETE_RE_LIST = [
    # Regex with dates must come before cause the regex for codes
    # catches also dates.
    ARRETE_DATE1_RE,
    ARRETE_DATE2_RE,
    ARRETE_CODE_AND_DATE1_RE,
    ARRETE_CODE_AND_DATE2_RE,
    ARRETE_CODE_RE,
]

ARRETE_IGNORE_RE = re.compile(r'(présent arrêté)|(par arrêté)|(arrêté\S)')


# TODO : also searches for known codes for arretes directly in text.
def _parse_arretes_references(
    soup: BeautifulSoup,
    children: List[PageElementOrString],
    arrete_re: Pattern,
) -> Iterator[PageElementOrString]:
    for child in children:
        if not isinstance(child, str):
            yield child
            continue

        for str_or_match in split_string_with_regex(arrete_re, child):
            if isinstance(str_or_match, str):
                yield str_or_match
                continue
            
            match_dict = str_or_match.groupdict()
            authority = cast(Authority, match_dict['authority'])
            if authority:
                assert authority in get_args(Authority), f'{authority} not in {get_args(Authority)}'
            code = parse_code(cast(CodeMatchDict, match_dict))
            qualifier = match_dict['qualifier']

            arrete_container = make_element(
                soup, ARRETE_REFERENCE_SCHEMA, dict(code=code, authority=authority, qualifier=qualifier)
            )
            
            for str_or_group in split_string_from_match(str_or_match):
                if isinstance(str_or_group, str):
                    arrete_container.append(str_or_group)
                elif str_or_group.name == 'date':
                    date = handle_date_match_groupdict(cast(DateMatchDict, match_dict))
                    if date is None:
                        raise RuntimeError(f"expected valid date in this match {str_or_match}")
                    arrete_container.append(make_date_element(soup, str_or_group.text, date))
                else:
                    arrete_container.append(str_or_group.text)

            yield arrete_container


def parse_arretes_references(
    soup: BeautifulSoup,
    children: List[PageElementOrString],
) -> List[PageElementOrString]:
    for arrete_re in ARRETE_RE_LIST:
        children = list(_parse_arretes_references(soup, children, arrete_re))
    return children