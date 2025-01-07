import re
from dataclasses import dataclass
from datetime import date
from bs4 import Tag, BeautifulSoup, NavigableString
from typing import Literal, List, get_args, cast, TypedDict, Pattern, Tuple, Iterator, Dict, Optional

from ..settings import APP_ROOT, LOGGER
from .dates import parse_date, DATE1_RES, DATE2_RES, DateMatchDict, handle_date_match_groupdict, make_date_element
from bench_convertisseur_xml.utils.text import normalize_text
from bench_convertisseur_xml.utils.html import PageElementOrString, make_data_tag
from bench_convertisseur_xml.utils.regex import split_string, split_match_by_named_groups, without_named_groups
from bench_convertisseur_xml.html_schemas import ARRETE_REFERENCE_SCHEMA

ARRETE_TYPES: List[str] = ['préfectoral', 'ministériel']

Authority = Literal['préfectoral', 'ministériel']

# code1 : matches all codes starting with n°
# code2 : match all codes of type 12-77LY87-7878 or 1L/77/9998
CODE_RES = r'(([nN]° ?(?P<code1>\S+))|(?P<code2>\S+[/\-]\S+))(?=\s|\.|$|,|\)|;)'

class CodeMatchDict(TypedDict):
    code1: str | None
    code2: str | None


def _parse_code(match_dict: CodeMatchDict) -> str | None:
    return match_dict.get('code1') or match_dict.get('code2')


class AuthorityMatchDict(TypedDict):
    authority: str | None


AUTHORITY_MAP: Dict[str, Authority] = {
    'ministériel': 'ministériel',
    'préfectoral': 'préfectoral',
    'ministériels': 'ministériel',
    'préfectoraux': 'préfectoral',
}

def _get_authority(match_dict: AuthorityMatchDict) -> Authority | None:
    authority_raw = match_dict.get('authority')
    if authority_raw:
        return AUTHORITY_MAP[authority_raw.lower()]
    else:
        return None


# It's important to capture this in the arrete reference regex, 
# so that we now it is not an action of modification, but rather
# part of the designation of the arrete.
MODIFIE_MODIFIANT = r'(modifié|modifiant)'
EN_DATE_DU = r'(du|en date du)'
ET_VIRGULE = r'(\s*(,|,?et)\s*)'

ARRETE_BASE_RES = r'arrêté ((?P<authority>préfectoral|ministériel) (modifié )?)?((?P<qualifier>complémentaire|d\'autorisation|d\'autorisation initial|de mise en demeure|de mesures d\'urgence) )?'
ARRETE_FILLER_RES = r'transmis a l\'exploitant par (courrier recommandé|courrier)'

ARRETE_DATE1_RE = re.compile(
    f'{ARRETE_BASE_RES}({ARRETE_FILLER_RES}\\s)?({EN_DATE_DU}\\s)?(?P<date>{DATE1_RES})(\\s{MODIFIE_MODIFIANT})?',
    re.IGNORECASE
)
ARRETE_DATE2_RE = re.compile(
    f'{ARRETE_BASE_RES}({ARRETE_FILLER_RES}\\s)?({EN_DATE_DU}\\s)?(?P<date>{DATE2_RES})(\\s{MODIFIE_MODIFIANT})?',
    re.IGNORECASE
)
ARRETE_CODE_AND_DATE1_RE = re.compile(
    f'{ARRETE_BASE_RES}({CODE_RES}\\s)({ARRETE_FILLER_RES}\\s)?({EN_DATE_DU}\\s)?(?P<date>{DATE1_RES})(\\s{MODIFIE_MODIFIANT})?',
    re.IGNORECASE
)
ARRETE_CODE_AND_DATE2_RE = re.compile(
    f'{ARRETE_BASE_RES}({CODE_RES}\\s)({ARRETE_FILLER_RES}\\s)?({EN_DATE_DU}\\s)?(?P<date>{DATE2_RES})(\\s{MODIFIE_MODIFIANT})?',
    re.IGNORECASE
)
ARRETE_CODE_RE = re.compile(f'{ARRETE_BASE_RES}{CODE_RES}', re.IGNORECASE)
ARRETE_RE_LIST = [
    # Regex with dates must come before cause the regex for codes
    # catches also dates.
    ARRETE_DATE1_RE,
    ARRETE_DATE2_RE,
    ARRETE_CODE_AND_DATE1_RE,
    ARRETE_CODE_AND_DATE2_RE,
    ARRETE_CODE_RE,
]

ARRETE_BASE_PLURAL_RES = r'arrêtés ((?P<authority>préfectoraux|ministériels) (modifiés )?)?'

ARRETE_PLURAL_DATE1_RES = f'({EN_DATE_DU}\\s)?(?P<date>{DATE1_RES})(\\s{MODIFIE_MODIFIANT})?'
ARRETE_PLURAL_DATE2_RES = f'({EN_DATE_DU}\\s)?(?P<date>{DATE2_RES})(\\s{MODIFIE_MODIFIANT})?'
ARRETE_PLURAL_CODE_AND_DATE1_RES = f'({CODE_RES}\\s)({EN_DATE_DU}\\s)?(?P<date>{DATE1_RES})(\\s{MODIFIE_MODIFIANT})?'
ARRETE_PLURAL_CODE_AND_DATE2_RES = f'({CODE_RES}\\s)({EN_DATE_DU}\\s)?(?P<date>{DATE2_RES})(\\s{MODIFIE_MODIFIANT})?'
ARRETE_PLURAL_CODE_RES = f'{CODE_RES}'
ARRETE_PLURAL_RES_LIST = [
    # Regex with dates must come before cause the regex for codes
    # catches also dates.
    ARRETE_PLURAL_CODE_AND_DATE1_RES,
    ARRETE_PLURAL_CODE_AND_DATE2_RES,
    ARRETE_PLURAL_DATE1_RES,
    ARRETE_PLURAL_DATE2_RES,
    ARRETE_PLURAL_CODE_RES,
]
ARRETE_PLURAL_RE = re.compile(f'{ARRETE_BASE_PLURAL_RES}(({'|'.join([ f'({without_named_groups(arrete_res)})' for arrete_res in ARRETE_PLURAL_RES_LIST ])}){ET_VIRGULE}?){{2,}}')
ARRETE_PLURAL_RE_LIST = [re.compile(regex) for regex in ARRETE_PLURAL_RES_LIST]

ARRETE_IGNORE_RE = re.compile(r'(présent arrêté)|(par arrêté)|(arrêté\S)')


# TODO : also searches for known codes for arretes directly in text.
def _parse_arretes_references(
    soup: BeautifulSoup,
    string: str,
    arrete_re: Pattern,
    default_data: Dict[str, str | None]=dict()
) -> Iterator[PageElementOrString]:
    for str_or_match in split_string(arrete_re, string):
        if isinstance(str_or_match, str):
            yield str_or_match
            continue
        
        tag_data: Dict[str, str | None] = dict(**default_data)
        tag_data.setdefault('authority', None)
        tag_data.setdefault('code', None)
        tag_data.setdefault('qualifier', None)

        match_dict = str_or_match.groupdict()
        tag_data['authority'] = _get_authority(cast(AuthorityMatchDict, match_dict)) or tag_data['authority']
        tag_data['code'] = _parse_code(cast(CodeMatchDict, match_dict)) or tag_data['code']
        tag_data['qualifier'] = match_dict.get('qualifier') or tag_data['qualifier']

        arrete_container = make_data_tag(
            soup, 
            ARRETE_REFERENCE_SCHEMA, 
            data=tag_data,
        )
        
        for str_or_group in split_match_by_named_groups(str_or_match):
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


def _parse_arretes_references_re_list(
    soup: BeautifulSoup,
    children: List[PageElementOrString],
    arrete_re_list: List[Pattern],
    default_data: Dict[str, str | None]=dict()
):
    new_children: List[PageElementOrString] = []
    for arrete_re in arrete_re_list:
        new_children = []
        for child in children:
            if isinstance(child, str):
                new_children.extend(list(_parse_arretes_references(soup, child, arrete_re, default_data)))
            else:
                new_children.append(child)
        children = new_children
    return children


def parse_arretes_references(
    soup: BeautifulSoup,
    children: List[PageElementOrString],
) -> List[PageElementOrString]:
    children = _parse_arretes_references_re_list(soup, children, ARRETE_RE_LIST)

    new_children: List[PageElementOrString] = []
    for child in children:
        if isinstance(child, str):
            for str_or_match in split_string(ARRETE_PLURAL_RE, child):
                if isinstance(str_or_match, str):
                    new_children.append(str_or_match)
                else:
                    match_dict = str_or_match.groupdict()
                    authority = _get_authority(cast(AuthorityMatchDict, match_dict))
                    new_children.extend(_parse_arretes_references_re_list(soup, [str_or_match.group(0)], ARRETE_PLURAL_RE_LIST, dict(authority=authority)))
        else:
            new_children.append(child)
    return new_children
