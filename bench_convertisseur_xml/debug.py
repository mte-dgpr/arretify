import re
from typing import Iterable, List, cast, Callable

from bs4 import BeautifulSoup

from .utils.text import remove_accents
from .utils.functional import flat_map_non_string, flat_map_string, Lambda
from .regex_utils import split_string_with_regex
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
        flat_map_string(
            children, 
            lambda string: flat_map_non_string(
                split_string_with_regex(pattern, string),
                Lambda[re.Match].cast(lambda match: [make_data_tag(
                    soup, 
                    DEBUG_KEYWORD_SCHEMA, 
                    contents=[match.group(0)],
                    data=dict(query=query)
                )])
            )
        )
    )