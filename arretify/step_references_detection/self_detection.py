from typing import Iterable, List

from bs4 import BeautifulSoup

from arretify.regex_utils import (
    regex_tree,
    map_regex_tree_match,
    split_string_with_regex_tree,
    iter_regex_tree_match_strings,
)
from arretify.types import PageElementOrString
from arretify.utils.functional import flat_map_string
from arretify.html_schemas import (
    DOCUMENT_REFERENCE_SCHEMA,
)
from arretify.utils.html import (
    make_data_tag,
    render_bool_attribute,
)
from arretify.law_data.types import (
    Document,
    DocumentType,
)
from arretify.law_data.uri import (
    render_uri,
    is_resolvable,
)


SELF_NODE = regex_tree.Group(
    regex_tree.Branching(
        [
            r"(le )?présent arrêté",
        ]
    ),
    group_name="__self",
)


def parse_self_references(
    soup: BeautifulSoup,
    children: Iterable[PageElementOrString],
) -> List[PageElementOrString]:
    document = Document(type=DocumentType.self)
    return list(
        flat_map_string(
            children,
            lambda string: map_regex_tree_match(
                split_string_with_regex_tree(SELF_NODE, string),
                lambda self_group_match: make_data_tag(
                    soup,
                    DOCUMENT_REFERENCE_SCHEMA,
                    data=dict(
                        uri=render_uri(document),
                        is_resolvable=render_bool_attribute(is_resolvable(document)),
                    ),
                    contents=iter_regex_tree_match_strings(self_group_match),
                ),
                allowed_group_names=["__self"],
            ),
        )
    )
