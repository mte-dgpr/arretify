import re
from typing import List, cast

import markdown
from bs4 import BeautifulSoup

from ..utils.html import PageElementOrString, make_element
from ..html_schemas import PARAGRAPH_SCHEMA, TABLE_SCHEMA


def clean_markdown(text: str) -> str:

    # Remove newline at the end
    text = re.sub(r'[\n\r]+$', '', text)

    # Remove * at the beginning only if not followed by space
    text = re.sub(r"^\*+(?!\s)", "", text)

    # Remove * at the end only if not preceded by space
    text = re.sub(r"(?<!\s)\*+$", "", text)

    # Remove any number of # or whitespaces at the beginning of the sentence
    text = re.sub(r"^[#\s]+", "", text)

    return text


def wrap_in_paragraphs(soup: BeautifulSoup, elements: List[PageElementOrString]):
    return [
        make_element(soup, PARAGRAPH_SCHEMA, contents=[element]) if isinstance(element, str) else element
        for element in elements if (not isinstance(element, str) or element.strip())
    ]


def parse_markdown_table(elements: List[PageElementOrString]):
    if [element for element in elements if not isinstance(element, str)]:
        raise ValueError(f'cannot parse markdown from beautifulsoup elements')
    str_elements = cast(List[str], elements)
    html_str = markdown.markdown(
        '\n'.join(str_elements), extensions=['tables']
    )
    soup = BeautifulSoup(html_str, features="html.parser")
    table_result = soup.select('table')
    if len(table_result) != 1:
        raise ValueError(f'invalid html results {html_str}')
    
    table_element = make_element(soup, TABLE_SCHEMA)
    table_element.extend(list(table_result[0].children))
    return table_element

