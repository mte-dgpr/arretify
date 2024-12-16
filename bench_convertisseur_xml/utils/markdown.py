import re
from typing import List, cast

import markdown
from bs4 import BeautifulSoup

from bench_convertisseur_xml.errors import ErrorCodes
from bench_convertisseur_xml.utils.html import PageElementOrString, make_element
from bench_convertisseur_xml.html_schemas import PARAGRAPH_SCHEMA, TABLE_SCHEMA, ERROR_SCHEMA


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


def parse_markdown_table(elements: List[PageElementOrString]):
    if [element for element in elements if not isinstance(element, str)]:
        raise ValueError(f'got unexpected non-string element to parse markdown from')

    markdown_str = '\n'.join(cast(List[str], elements))
    html_str = markdown.markdown(markdown_str, extensions=['tables'])
    soup = BeautifulSoup(html_str, features="html.parser")
    table_result = soup.select('table')
    if len(table_result) != 1:
        error_element = make_element(soup, ERROR_SCHEMA, dict(error_code=ErrorCodes.markdown_parsing.value), contents=[markdown_str])
        error_container = make_element(soup, PARAGRAPH_SCHEMA, contents=[error_element])
        return error_container
    
    table_element = make_element(soup, TABLE_SCHEMA)
    table_element.extend(list(table_result[0].children))
    return table_element

