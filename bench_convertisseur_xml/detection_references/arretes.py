import re
from dataclasses import dataclass
from datetime import date
from typing import Literal, List, get_args, cast, TypedDict, Pattern, Tuple

from ..settings import APP_ROOT, LOGGER
from .text_utils import remove_accents, normalize_text
from .parse_date import parse_date, DATE1_RE, DATE2_RE

# TODO : also searches for known codes for arretes directly in text.


ARRETE_TYPES: List[str] = ['prefectoral', 'ministeriel']

RefType = Literal['article']
Authority = Literal['prefectoral', 'ministeriel']

@dataclass
class ArreteReference: 
    date: date | None
    authority: Authority | None
    qualifier: str | None
    """
    e.g.: "complementaire", "d'autorisation", etc.
    """

    code: str | None


# articles 6.18.1 à 6.18.7 de l'annexe 2 à l'arrêté préfectoral 98/C/014 du 22 janvier 1998
# 2ème alinéa de l'article 4.1.b de l'arrêté 90/IC/035
# l'article 4.1.f de l'arrêté 90/IC/035
# l'arrêté préfectoral 90/IC/035 du 22 février 1990

# premier alinéa de l'article 4.1. c de l'arrêté 90/IC/035
# 4ème alinéa de l'article 4.1 c de l'arrêté 90/IC/035
# l'article 4.1.c de l'arrêté 90/IC/035

# articles 3 à 11 de l'arrêté ministériel du 10 mai 1993 relatif aux stockages de gaz inflammables liquéfiés

# l'article 8 de ce même arrêté ministériel

# l'article 11 de l'arrêté ministériel

# loi du 19 juillet 1976

# arrete ministeriel du 2 fevrier 1998


# code1 : matches all codes starting with n°
# code2 : match all codes of type 12-77LY87-7878 or 1L/77/9998
CODE_RE = r'(([nN]° ?(?P<code1>\S+))|(?P<code2>\S+[/\-]\S+))(\s|$)'


class CodeMatchDict(TypedDict):
    code1: str
    code2: str


def parse_code(match_dict: CodeMatchDict):
    return match_dict.get('code1') or match_dict.get('code2')


ARRETE_BASE_RE = r'arrete ((?P<authority>prefectoral|ministeriel) (modifie )?)?((?P<qualifier>complementaire|d\'autorisation|d\'autorisation initial|de mise en demeure|de mesures d\'urgence) )?'
ARRETE_FILLER_RE = r'(transmis a l\'exploitant par (courrier recommande|courrier) )?((du|en date du) )?'

ARRETE_DATE1_RE = re.compile(
    f'{ARRETE_BASE_RE}{ARRETE_FILLER_RE}{DATE1_RE}'
)
ARRETE_DATE2_RE = re.compile(
    f'{ARRETE_BASE_RE}{ARRETE_FILLER_RE}{DATE2_RE}'
)
ARRETE_CODE_AND_DATE1_RE = re.compile(
    f'{ARRETE_BASE_RE}{CODE_RE}{ARRETE_FILLER_RE}{DATE1_RE}'
)
ARRETE_CODE_AND_DATE2_RE = re.compile(
    f'{ARRETE_BASE_RE}{CODE_RE}{ARRETE_FILLER_RE}{DATE2_RE}'
)
ARRETE_CODE_RE = re.compile(f'{ARRETE_BASE_RE}{CODE_RE}')

ARRETE_RE_LIST = [
    # Regex with dates must come before cause the regex for codes
    # catches also dates.
    ARRETE_DATE1_RE,
    ARRETE_DATE2_RE,
    ARRETE_CODE_AND_DATE1_RE,
    ARRETE_CODE_AND_DATE2_RE,
    ARRETE_CODE_RE,
]

ARRETE_IGNORE_RE = re.compile(r'(present arrete)|(par arrete)|(arrete\S)')

def parse_arretes(arrete_re_list: List[Pattern], text: str) -> Tuple[List[ArreteReference], str | None]:
    arretes_refs: List[ArreteReference] = []
    arretes_failed: List[str] = []
    remainder = text
    for arrete_re in arrete_re_list:
        matches, remainder = normalize_text(arrete_re, remainder, '<ArreteRef>')
        for match in matches:
            match_dict = match.groupdict()

            authority = cast(Authority, match_dict['authority'])
            if authority:
                assert authority in get_args(Authority), f'{authority} not in {get_args(Authority)}'

            reference = ArreteReference(
                date=parse_date(match_dict), 
                authority=authority,
                qualifier=match_dict['qualifier'],
                code=parse_code(match_dict),
            )
            arretes_refs.append(reference)

    matches, remainder = normalize_text(ARRETE_IGNORE_RE, remainder, '<ArreteIgnored>')
    if 'arrete' in remainder:
        return arretes_refs, remainder
    else:
        return arretes_refs, None