from typing import Iterable, List

from bs4 import BeautifulSoup

from bench_convertisseur_xml.regex_utils import regex_tree, flat_map_regex_tree_match, split_string_with_regex_tree, iter_regex_tree_match_strings
from bench_convertisseur_xml.regex_utils.helpers import join_with_or, lookup_normalized_version
from bench_convertisseur_xml.types import PageElementOrString
from bench_convertisseur_xml.utils.functional import flat_map_string
from bench_convertisseur_xml.html_schemas import DOCUMENT_REFERENCE_SCHEMA
from bench_convertisseur_xml.utils.html import make_data_tag
from bench_convertisseur_xml.law_data.types import EuActDocument
from bench_convertisseur_xml.law_data.uri import render_uri
from bench_convertisseur_xml.law_data.eurlex_constants import EU_ACT_DOMAINS, EU_ACT_TYPES

# Examples : CE, UE, ...
DOMAIN_NODE = regex_tree.Literal(
    r'(?P<domain>' + join_with_or(EU_ACT_DOMAINS) + ')',
)


# REF : https://style-guide.europa.eu/fr/content/-/isg/topic?identifier=1.2.2-numbering-of-acts
# We are more lenient than the official style guide, as many references do not follow it.
IDENTIFIER_NODE = regex_tree.Literal(
    r'(?P<identifier>[0-9]+/[0-9]+)',
)


EU_ACT_NODE = regex_tree.Group(
    regex_tree.Sequence([
        # Examples : 
        # règlement
        # directive
        r'(?P<act_type>' + join_with_or(EU_ACT_TYPES) + ')\s+(européen(ne)?\s+)?',

        # Order matters cause second alternative matches also the first one.
        regex_tree.Branching([
            # Examples :
            # 2010/75/UE
            regex_tree.Sequence([
                r'([nN]°\s*)?',
                IDENTIFIER_NODE,
                r'/', 
                DOMAIN_NODE,
            ]),

            # Examples : 
            # (CE) n° 1013/2006
            # (CE) 1013/2006
            # n° 1013/2006
            # 1013/2006 
            regex_tree.Sequence([
                regex_tree.Quantifier(
                    regex_tree.Sequence([r'\(', DOMAIN_NODE, r'\)\s*']),
                    quantifier='?',
                ), 
                r'([nN]°\s*)?',
                IDENTIFIER_NODE
            ]),
        ])
    ]),
    group_name='__eu_act',
)


def parse_eu_acts_references(
    soup: BeautifulSoup,
    children: Iterable[PageElementOrString],
) -> List[PageElementOrString]:
    return list(flat_map_string(
        children,
        lambda string: flat_map_regex_tree_match(
            split_string_with_regex_tree(EU_ACT_NODE, string),
            lambda eu_act_group_match: [
                _render_eu_act_container(
                    soup, 
                    eu_act_group_match,
                ),
            ],
            allowed_group_names=['__eu_act'],
        )
    ))


def _render_eu_act_container(
    soup: BeautifulSoup,
    eu_act_group_match: regex_tree.Match,
) -> PageElementOrString:
    match_dict = eu_act_group_match.match_dict
    document = EuActDocument(
        act_type=lookup_normalized_version(EU_ACT_TYPES, match_dict['act_type']),
        identifier=match_dict['identifier'],
        domain=match_dict.get('domain', None),
    )
    return make_data_tag(
        soup, 
        DOCUMENT_REFERENCE_SCHEMA,
        data=dict(uri=render_uri(document)),
        contents=iter_regex_tree_match_strings(eu_act_group_match),
    )