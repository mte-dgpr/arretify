import re
from dataclasses import dataclass
from datetime import date
from bs4 import Tag, BeautifulSoup
from typing import Literal, List, Tuple, Iterator, Dict, Optional, Iterable, Union, cast

from ..settings import APP_ROOT, LOGGER
from bench_convertisseur_xml.utils.html import PageElementOrString, make_data_tag, render_bool_attribute
from bench_convertisseur_xml.utils.functional import flat_map_string
from bench_convertisseur_xml.html_schemas import DOCUMENT_REFERENCE_SCHEMA
from bench_convertisseur_xml.parsing_utils.patterns import ET_VIRGULE_PATTERN_S
from bench_convertisseur_xml.parsing_utils.dates import DATE_NODE, render_date_regex_tree_match
from bench_convertisseur_xml.regex_utils import regex_tree, flat_map_regex_tree_match, split_string_with_regex_tree
from bench_convertisseur_xml.law_data.types import Document, DocumentType
from bench_convertisseur_xml.law_data.uri import render_uri, is_resolvable

Authority = Literal['préfectoral', 'ministériel']

Code = str

AUTHORITY_MAP: Dict[str, Authority] = {
    'ministériel': 'ministériel',
    'préfectoral': 'préfectoral',
    'ministériels': 'ministériel',
    'préfectoraux': 'préfectoral',
}


IDENTIFIER_NODE = regex_tree.Sequence([
    regex_tree.Branching([
        # Matches all codes starting with n°
        r'[nN]° ?(?P<identifier>\S+)',
        # Matches all codes of type 12-77LY87-7878 or 1L/77/9998
        r'(?P<identifier>\S+[/\-]\S+)',
    ]),
    r'(?=\s|\.|$|,|\)|;)',
])


ARRETE_NODE = regex_tree.Group(regex_tree.Sequence([
    r'arrêté ((?P<authority>préfectoral|ministériel) (modifié )?)?((?P<qualifier>complémentaire|d\'autorisation initiale?|d\'autorisation|de mise en demeure|de mesures d\'urgence) )?',
    regex_tree.Branching([
        regex_tree.Sequence([
            regex_tree.Quantifier(
                regex_tree.Sequence([
                    IDENTIFIER_NODE,
                    '\s',
                ]), 
                '?',
            ),
            r'(transmis a l\'exploitant par (courrier recommandé|courrier)\s)?',
            regex_tree.Sequence([
                r'((du|en date du)\s)?',
                DATE_NODE,
            ]),
            # It's important to capture this in the arrete reference regex, 
            # so that we now it is not an action of modification, but rather
            # part of the designation of the arrete.
            r'(\s(modifié|modifiant)(?=\b))?',
        ]),

        IDENTIFIER_NODE,
    ]),
]), group_name='__arrete')


ARRETE_MULTIPLE_NODE = regex_tree.Group(regex_tree.Sequence([
    r'arrêtés ((?P<authority>préfectoraux|ministériels) (modifiés )?)?',
    regex_tree.Quantifier(
        regex_tree.Sequence([
            regex_tree.Group(
                regex_tree.Branching([
                    # Regex with dates must come before cause the regex for codes
                    # catches also dates.
                    regex_tree.Sequence([
                        regex_tree.Quantifier(
                            regex_tree.Sequence([
                                IDENTIFIER_NODE,
                                '\s',
                            ]),
                            '?',
                        ),
                        regex_tree.Sequence([
                            r'((du|en date du)\s)?',
                            DATE_NODE,
                        ]),
                        r'(\s(modifié|modifiant))?',
                    ]),

                    IDENTIFIER_NODE,
                ]), group_name='__arrete'
            ),
            f'{ET_VIRGULE_PATTERN_S}?',
        ]), 
        '{2,}',
    )
]), group_name='__arrete_multiple')


def _extract_identifier(arrete_match: regex_tree.Match) -> Union[Code, None]:
    return arrete_match.match_dict.get('identifier', None)


def _render_arrete_container(
    soup: BeautifulSoup, 
    arrete_match: regex_tree.Match, 
    base_arrete_match: regex_tree.Match
) -> Tag:
    # Parse date tag and extract date value
    arrete_tag_contents = list(flat_map_regex_tree_match(
        arrete_match.children,
        lambda date_group_match: [
            render_date_regex_tree_match(soup, date_group_match)
        ],
        allowed_group_names=[DATE_NODE.group_name],
    ))

    arrete_date: Optional[str] = None
    for tag_or_str in arrete_tag_contents:
        if isinstance(tag_or_str, Tag) and tag_or_str.name == 'time':
            arrete_date = cast(str, tag_or_str['datetime'])
            break

    # Build the arrete document object
    authority_raw = base_arrete_match.match_dict.get('authority')
    if authority_raw in ['ministériels', 'ministériel']:
        document_type = DocumentType.arrete_ministeriel
    elif authority_raw in ['préfectoraux', 'préfectoral']:
        document_type = DocumentType.arrete_prefectoral
    else:
        document_type = DocumentType.unknown_arrete
    
    document = Document(
        type=document_type,
        num=_extract_identifier(arrete_match),
        date=arrete_date,
    )

    # Render the arrete tag
    return make_data_tag(
        soup, 
        DOCUMENT_REFERENCE_SCHEMA,
        data=dict(
            uri=render_uri(document),
            is_resolvable=render_bool_attribute(is_resolvable(document)),
        ),
        contents=arrete_tag_contents,
    )


def _parse_arretes_references(
    soup: BeautifulSoup,
    children: Iterable[PageElementOrString],
):
    return flat_map_string(
        children,
        lambda string: flat_map_regex_tree_match(
            split_string_with_regex_tree(ARRETE_NODE, string),
            lambda arrete_container_group_match: [
                _render_arrete_container(
                    soup, 
                    arrete_container_group_match, 
                    arrete_container_group_match,
                ),
            ],
            allowed_group_names=['__arrete'],
        )
    )


def _parse_multiple_arretes_references(
    soup: BeautifulSoup,
    children: Iterable[PageElementOrString],
):
    # For multiple arretes, we need to first parse some of the attributes in common
    # before parsing each individual arrete reference.
    return flat_map_string(
        children,
        lambda string: flat_map_regex_tree_match(
            split_string_with_regex_tree(ARRETE_MULTIPLE_NODE, string),
            lambda arrete_multiple_group_match: flat_map_regex_tree_match(
                arrete_multiple_group_match.children,
                lambda arrete_container_group_match: [
                    _render_arrete_container(
                        soup, 
                        arrete_container_group_match, 
                        arrete_multiple_group_match,
                    )
                ],
                allowed_group_names=['__arrete'],
            ),
            allowed_group_names=['__arrete_multiple'],
        )
    )


def parse_arretes_references(
    soup: BeautifulSoup,
    children: Iterable[PageElementOrString],
) -> List[PageElementOrString]:
    # First check for multiple, cause it is the most exhaustive pattern
    new_children = list(_parse_multiple_arretes_references(soup, children))
    return list(_parse_arretes_references(soup, new_children))
