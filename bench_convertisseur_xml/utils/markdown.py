import re
from typing import List, cast

import markdown
from bs4 import BeautifulSoup

from bench_convertisseur_xml.errors import ErrorCodes
from bench_convertisseur_xml.utils.html import PageElementOrString, make_element
from bench_convertisseur_xml.html_schemas import ERROR_SCHEMA


def parse_markdown_table(elements: List[PageElementOrString]):
    if [element for element in elements if not isinstance(element, str)]:
        raise ValueError(f'got unexpected non-string element to parse markdown from')

    markdown_str = '\n'.join(cast(List[str], elements))
    html_str = markdown.markdown(markdown_str, extensions=['tables'])
    soup = BeautifulSoup(html_str, features="html.parser")
    table_result = soup.select('table')
    if len(table_result) != 1:
        return make_element(
            soup, 
            ERROR_SCHEMA, 
            dict(error_code=ErrorCodes.markdown_parsing.value), contents=[markdown_str]
        )
    
    table_element = soup.new_tag('table')
    table_element.extend(list(table_result[0].children))
    return table_element

