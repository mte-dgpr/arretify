from typing import Iterable, List, Optional, cast

from bs4 import BeautifulSoup, Tag

from bench_convertisseur_xml.regex_utils import regex_tree, flat_map_regex_tree_match, split_string_with_regex_tree
from bench_convertisseur_xml.parsing_utils.dates import DATE_NODE, render_date_regex_tree_match
from bench_convertisseur_xml.types import PageElementOrString
from bench_convertisseur_xml.utils.functional import flat_map_string
from bench_convertisseur_xml.html_schemas import DOCUMENT_REFERENCE_SCHEMA
from bench_convertisseur_xml.utils.html import make_data_tag
from bench_convertisseur_xml.law_data.types import DecretDocument
from bench_convertisseur_xml.law_data.uri import render_uri


# Examples :
# décret n°2005-635 du 30 mai 2005
DECRET_NODE = regex_tree.Group(
    regex_tree.Sequence([
        r'décret\s+',
        r'(n\s*°\s*(?P<identifier>[\d\-]+)\s+)?',
        r'du\s+',
        DATE_NODE,
    ]),
    group_name='__decret',
)


def parse_decrets_references(
    soup: BeautifulSoup,
    children: Iterable[PageElementOrString],
) -> List[PageElementOrString]:
    return list(flat_map_string(
        children,
            lambda string: flat_map_regex_tree_match(
            split_string_with_regex_tree(DECRET_NODE, string),
            lambda decret_match: [
                _render_decret_container(
                    soup, 
                    decret_match,
                ),
            ],
            allowed_group_names=['__decret'],
        )
    ))


def _render_decret_container(
    soup: BeautifulSoup,
    decret_match: regex_tree.Match,
) -> PageElementOrString:
    # Parse date tag and extract date value
    decret_tag_contents = list(flat_map_regex_tree_match(
        decret_match.children,
        lambda date_match: [
            render_date_regex_tree_match(soup, date_match)
        ],
        allowed_group_names=[DATE_NODE.group_name],
    ))

    decret_date: Optional[str] = None
    for tag_or_str in decret_tag_contents:
        if isinstance(tag_or_str, Tag) and tag_or_str.name == 'time':
            decret_date = cast(str, tag_or_str['datetime'])
            break
    if decret_date is None:
        raise ValueError('Could not find decret date')

    document = DecretDocument(
        date=decret_date,
        identifier=decret_match.match_dict.get('identifier', None),
    )

    return make_data_tag(
        soup, 
        DOCUMENT_REFERENCE_SCHEMA,
        data=dict(uri=render_uri(document)),
        contents=decret_tag_contents,
    )