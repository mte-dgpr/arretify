import re
from typing import Dict, List, Optional, Union

from bs4 import BeautifulSoup, PageElement

from ..html_schemas import PARAGRAPH_SCHEMA
from ..types import DataElementSchema, PresentationElementSchema


PageElementOrString = Union[PageElement, str]


def make_css_class(schema: DataElementSchema):
    return f'dsr-{schema.name}'


def make_element(
    soup: BeautifulSoup, 
    schema: DataElementSchema | PresentationElementSchema, 
    data: Dict[str, str | None]=dict(), 
    contents: List[PageElementOrString] | None=None,
):
    element = soup.new_tag(schema.tag_name)
    if isinstance(schema, DataElementSchema):
        element['class'] = [make_css_class(schema)]
    if isinstance(schema, DataElementSchema):
        for key in schema.data_keys:
            data_value = data[key]
            if data_value is not None:
                element[f'data-{key}'] = data_value
    if contents:
        element.extend(contents)
    return element


def wrap_in_paragraphs(soup: BeautifulSoup, elements: List[PageElementOrString]):
    return [
        make_element(soup, PARAGRAPH_SCHEMA, contents=[element]) if isinstance(element, str) else element
        for element in elements if (not isinstance(element, str) or element.strip())
    ]

