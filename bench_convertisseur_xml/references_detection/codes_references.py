from typing import Iterable, List

from bs4 import BeautifulSoup

from bench_convertisseur_xml.law_data.legifrance import get_code_titles
from bench_convertisseur_xml.regex_utils import regex_tree, flat_map_regex_tree_match, split_string_with_regex_tree, iter_regex_tree_match_strings
from bench_convertisseur_xml.regex_utils.helpers import lookup_normalized_version
from bench_convertisseur_xml.types import PageElementOrString
from bench_convertisseur_xml.utils.functional import flat_map_string
from bench_convertisseur_xml.html_schemas import DOCUMENT_REFERENCE_SCHEMA
from bench_convertisseur_xml.utils.html import make_data_tag
from bench_convertisseur_xml.law_data.types import CodeDocument
from bench_convertisseur_xml.law_data.uri import render_uri
from bench_convertisseur_xml.law_data.external_urls import resolve_external_url


# TODO: Makes parsing very slow, because compiles into a big OR regex.
CODE_NODE = regex_tree.Group(
    regex_tree.Branching([
        f'(?P<title>{code})' for code in get_code_titles()
    ]),
    group_name='__code',
)


def parse_codes_references(
    soup: BeautifulSoup,
    children: Iterable[PageElementOrString],
) -> List[PageElementOrString]:
    return list(flat_map_string(
        children,
            lambda string: flat_map_regex_tree_match(
            split_string_with_regex_tree(CODE_NODE, string),
            lambda code_group_match: [
                _render_code_reference(
                    soup, 
                    code_group_match,
                ),
            ],
            allowed_group_names=['__code'],
        )
    ))


def _render_code_reference(
    soup: BeautifulSoup,
    code_group_match: regex_tree.Match,
) -> PageElementOrString:
    title = lookup_normalized_version(
        get_code_titles(), 
        code_group_match.match_dict['title']
    )
    document = CodeDocument(
        title=title,
    )
    external_url = resolve_external_url(document)
    code_reference_tag = make_data_tag(
        soup, 
        DOCUMENT_REFERENCE_SCHEMA,
        data=dict(uri=render_uri(document)),
        contents=iter_regex_tree_match_strings(code_group_match),
    )
    if external_url is not None:
        code_reference_tag['href'] = external_url
    return code_reference_tag