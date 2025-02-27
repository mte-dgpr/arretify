from typing import Iterable, List

from bs4 import BeautifulSoup

from bench_convertisseur_xml.regex_utils import regex_tree, flat_map_regex_tree_match, split_string_with_regex_tree, iter_regex_tree_match_strings
from bench_convertisseur_xml.types import PageElementOrString
from bench_convertisseur_xml.utils.functional import flat_map_string
from bench_convertisseur_xml.html_schemas import DOCUMENT_REFERENCE_SCHEMA
from bench_convertisseur_xml.utils.html import make_data_tag
from bench_convertisseur_xml.uri import render_uri, Self


SELF_NODE = regex_tree.Group(
    regex_tree.Branching([
        r'(le )?présent arrêté',
    ]),
    group_name='__self',
)


def parse_self_references(
    soup: BeautifulSoup,
    children: Iterable[PageElementOrString],
) -> List[PageElementOrString]:
    return list(flat_map_string(
        children,
            lambda string: flat_map_regex_tree_match(
            split_string_with_regex_tree(SELF_NODE, string),
            lambda self_group_match: [
                make_data_tag(
                    soup, 
                    DOCUMENT_REFERENCE_SCHEMA,
                    data=dict(uri=render_uri(Self())),
                    contents=iter_regex_tree_match_strings(self_group_match),
                ),
            ],
            allowed_group_names=['__self'],
        )
    ))