import re
from dataclasses import dataclass
from datetime import date
from bs4 import Tag, BeautifulSoup
from typing import Literal, List, get_args, cast, TypedDict, Pattern, Tuple, Iterator, Dict, Optional, Iterable

from ..settings import APP_ROOT, LOGGER
from bench_convertisseur_xml.utils.html import PageElementOrString, make_data_tag
from bench_convertisseur_xml.utils.split import split_string_with_regex, split_match_by_named_groups, reduce_children
from bench_convertisseur_xml.utils.functional import flat_map_non_string, flat_map_string, Lambda
from bench_convertisseur_xml.utils.regex import without_named_groups_many, join_with_or
from bench_convertisseur_xml.html_schemas import ARRETE_REFERENCE_SCHEMA
from bench_convertisseur_xml.parsing_misc.patterns import ET_VIRGULE_PATTERN_S
from bench_convertisseur_xml.parsing_misc.dates import DATE_NODE, render_date_match_group
from bench_convertisseur_xml import regex_engine as ree

Authority = Literal['préfectoral', 'ministériel']

AUTHORITY_MAP: Dict[str, Authority] = {
    'ministériel': 'ministériel',
    'préfectoral': 'préfectoral',
    'ministériels': 'ministériel',
    'préfectoraux': 'préfectoral',
}


CODE_NODE = ree.Sequence([
    ree.Branching([
        # Matches all codes starting with n°
        r'[nN]° ?(?P<code>\S+)',
        # Matches all codes of type 12-77LY87-7878 or 1L/77/9998
        r'(?P<code>\S+[/\-]\S+)',
    ]),
    r'(?=\s|\.|$|,|\)|;)',
])


ARRETE_NODE = ree.Group(ree.Sequence([
    r'arrêté ((?P<authority>préfectoral|ministériel) (modifié )?)?((?P<qualifier>complémentaire|d\'autorisation initiale?|d\'autorisation|de mise en demeure|de mesures d\'urgence) )?',
    ree.Branching([
        ree.Sequence([
            ree.Quantifier(
                ree.Sequence([
                    CODE_NODE,
                    '\s',
                ]), 
                '?',
            ),
            r'(transmis a l\'exploitant par (courrier recommandé|courrier)\s)?',
            ree.Sequence([
                r'((du|en date du)\s)?',
                DATE_NODE,
            ]),
            # It's important to capture this in the arrete reference regex, 
            # so that we now it is not an action of modification, but rather
            # part of the designation of the arrete.
            r'(\s(modifié|modifiant))?',
        ]),

        CODE_NODE,
    ]),
]), group_name='__arrete')


ARRETE_PLURAL_NODE = ree.Group(ree.Sequence([
    r'arrêtés ((?P<authority>préfectoraux|ministériels) (modifiés )?)?',
    ree.Quantifier(
        ree.Sequence([
            ree.Group(
                ree.Branching([
                    # Regex with dates must come before cause the regex for codes
                    # catches also dates.
                    ree.Sequence([
                        ree.Quantifier(
                            ree.Sequence([
                                CODE_NODE,
                                '\s',
                            ]),
                            '?',
                        ),
                        ree.Sequence([
                            r'((du|en date du)\s)?',
                            DATE_NODE,
                        ]),
                        r'(\s(modifié|modifiant))?',
                    ]),

                    CODE_NODE,
                ]), group_name='__arrete'
            ),
            f'{ET_VIRGULE_PATTERN_S}?',
        ]), 
        '{2,}',
    )
]), group_name='__arrete_plural')


def _handle_arrete_base_match_dict(match_dict: ree.MatchDict) -> Dict:
    authority_raw = match_dict.get('authority')
    if authority_raw:
        authority = AUTHORITY_MAP[authority_raw.lower()]
    else:
        authority = None
    qualifier = match_dict.get('qualifier')
    return dict(qualifier=qualifier, authority=authority)


def _handle_arrete_details_match_dict(match_dict: ree.MatchDict) -> Dict:
    return dict(code=match_dict.get('code'))


def _render_arrete_container_match_group(
    soup: BeautifulSoup, 
    match_group: ree.MatchGroup, 
    base_arrete_match_dict: ree.MatchDict
) -> Tag:
    return make_data_tag(
        soup, 
        ARRETE_REFERENCE_SCHEMA,
        data=dict(
            **base_arrete_match_dict,
            **_handle_arrete_details_match_dict(match_group.match_dict),
        ),
        contents=list(ree.flat_map_match_group(
            match_group.children,
            lambda date_group_match: [render_date_match_group(soup, date_group_match)],
            allowed_group_names=[DATE_NODE.group_name],
        )),
    )


def _parse_arretes_references(
    soup: BeautifulSoup,
    children: Iterable[PageElementOrString],
):
    return flat_map_string(
        children,
        lambda string: ree.flat_map_match_group(
            ree.split_string(ARRETE_NODE, string),
            lambda arrete_container_group_match: [
                _render_arrete_container_match_group(
                    soup, 
                    arrete_container_group_match, 
                    _handle_arrete_base_match_dict(arrete_container_group_match.match_dict),
                ),
            ],
            allowed_group_names=['__arrete'],
        )
    )


def _parse_plural_arretes_references(
    soup: BeautifulSoup,
    children: Iterable[PageElementOrString],
):
    # For plural arretes, we need to first parse some of the attributes in common
    # before parsing each individual arrete reference.
    return flat_map_string(
        children,
        lambda string: ree.flat_map_match_group(
            ree.split_string(ARRETE_PLURAL_NODE, string),
            lambda arrete_plural_group_match: ree.flat_map_match_group(
                arrete_plural_group_match.children,
                lambda arrete_container_group_match: [
                    _render_arrete_container_match_group(
                        soup, 
                        arrete_container_group_match, 
                        _handle_arrete_base_match_dict(arrete_plural_group_match.match_dict),
                    )
                ],
                allowed_group_names=['__arrete'],
            ),
            allowed_group_names=['__arrete_plural'],
        )
    )


def parse_arretes_references(
    soup: BeautifulSoup,
    children: Iterable[PageElementOrString],
) -> List[PageElementOrString]:
    # First check for plural, cause it is the most exhaustive pattern
    new_children = list(_parse_plural_arretes_references(soup, children))
    return list(_parse_arretes_references(soup, new_children))
