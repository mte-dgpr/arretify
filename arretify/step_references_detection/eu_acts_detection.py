#
# Copyright (c) 2025 Direction générale de la prévention des risques (DGPR).
#
# This file is part of Arrêtify.
# See https://github.com/mte-dgpr/arretify for further info.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from typing import Iterable, List

from bs4 import BeautifulSoup

from arretify.regex_utils import (
    regex_tree,
    map_regex_tree_match,
    split_string_with_regex_tree,
    iter_regex_tree_match_strings,
)
from arretify.regex_utils.helpers import (
    join_with_or,
    lookup_normalized_version,
)
from arretify.parsing_utils.dates import (
    parse_year_str,
    render_year_str,
)
from arretify.types import PageElementOrString, DocumentContext
from arretify.utils.functional import flat_map_string
from arretify.html_schemas import (
    DOCUMENT_REFERENCE_SCHEMA,
)
from arretify.utils.html import (
    make_data_tag,
)
from arretify.law_data.types import (
    Document,
    DocumentType,
)
from arretify.law_data.uri import (
    render_uri,
)
from arretify.law_data.eurlex_constants import (
    EU_ACT_DOMAINS,
    EU_ACT_TYPES,
)

# Examples : CE, UE, ...
DOMAIN_NODE = regex_tree.Literal(
    r"(?P<domain>" + join_with_or(EU_ACT_DOMAINS) + ")",
)

# REF :
# https://style-guide.europa.eu/fr/content/-/isg/topic?identifier=1.2.2-numbering-of-acts
# https://style-guide.europa.eu/fr/content/-/isg/topic?identifier=summary-tables
# We are more lenient than the official style guide, as many references do not follow it.
EU_ACT_NODE = regex_tree.Group(
    regex_tree.Sequence(
        [
            # Examples :
            # règlement
            # directive
            r"(?P<act_type>" + join_with_or(EU_ACT_TYPES) + r")\s+(européen(ne)?\s+)?",
            # Order matters cause second alternative matches also the first one.
            regex_tree.Branching(
                [
                    # Examples :
                    # 2010/75/UE
                    regex_tree.Sequence(
                        [
                            r"([nN]°\s*)?",
                            r"(?P<year>[0-9]{4}|[0-9]{2})/(?P<num>[0-9]+)",
                            r"/",
                            DOMAIN_NODE,
                        ]
                    ),
                    # Examples :
                    # (CE) n° 1013/2006
                    # (CE) 1013/2006
                    # n° 1013/2006
                    # 1013/2006
                    regex_tree.Sequence(
                        [
                            regex_tree.Repeat(
                                regex_tree.Sequence([r"\(", DOMAIN_NODE, r"\)\s*"]),
                                quantifier=(0, 1),
                            ),
                            r"([nN]°\s*)?",
                            r"(?P<num>[0-9]+)/(?P<year>[0-9]{4}|[0-9]{2})",
                            # Check that the date string is followed by a valid separator
                            # so that we don't match strings like 23/2003/POIPOIPOI.
                            r"(?=\s|\.|$|,|\)|;)",
                        ]
                    ),
                ]
            ),
        ]
    ),
    group_name="__eu_act",
)


def parse_eu_acts_references(
    document_context: DocumentContext,
    children: Iterable[PageElementOrString],
) -> List[PageElementOrString]:
    return list(
        flat_map_string(
            children,
            lambda string: map_regex_tree_match(
                split_string_with_regex_tree(EU_ACT_NODE, string),
                lambda eu_act_group_match: _render_eu_act_reference(
                    document_context.soup,
                    eu_act_group_match,
                ),
                allowed_group_names=["__eu_act"],
            ),
        )
    )


def _render_eu_act_reference(
    soup: BeautifulSoup,
    eu_act_group_match: regex_tree.Match,
) -> PageElementOrString:
    match_dict = eu_act_group_match.match_dict
    act_type = lookup_normalized_version(EU_ACT_TYPES, match_dict["act_type"])
    if act_type == "règlement":
        document_type = DocumentType.eu_regulation
    elif act_type == "directive":
        document_type = DocumentType.eu_directive
    elif act_type == "décision":
        document_type = DocumentType.eu_decision
    else:
        raise ValueError(f"Unknown EU act type {act_type}")

    year = parse_year_str(match_dict["year"])
    document = Document(
        type=document_type,
        num=match_dict["num"],
        date=render_year_str(year),
    )
    return make_data_tag(
        soup,
        DOCUMENT_REFERENCE_SCHEMA,
        data=dict(
            uri=render_uri(document),
        ),
        contents=iter_regex_tree_match_strings(eu_act_group_match),
    )
