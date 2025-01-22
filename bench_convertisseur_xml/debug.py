import re
from typing import Iterable, List

from bs4 import BeautifulSoup

from .utils.text import remove_accents
from .utils.split import map_match_flow, split_string_with_regex, map_string_children
from .utils.html import make_data_tag
from .html_schemas import DEBUG_KEYWORD_SCHEMA
from .types import PageElementOrString


def insert_debug_keywords(
    soup: BeautifulSoup,
    children: Iterable[PageElementOrString],
    query: str,
) -> List[PageElementOrString]:
    unaccented = remove_accents(query)
    pattern = re.compile(f'{query}|{unaccented}', re.IGNORECASE)
    return list(
        map_string_children(
            children, 
            lambda string: map_match_flow(
                split_string_with_regex(string, pattern),
                lambda match: [make_data_tag(
                    soup, 
                    DEBUG_KEYWORD_SCHEMA, 
                    contents=[match.group(0)], 
                    data=dict(query=query)
                )]
            )
        )
    )