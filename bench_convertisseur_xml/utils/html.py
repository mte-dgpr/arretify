import re
from typing import Dict, List, Optional, Union

from bs4 import BeautifulSoup, PageElement, Tag

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
    wrapped: List[Tag] = []
    for element in elements:
        if isinstance(element, str) and element.strip():
            p = soup.new_tag('p')
            wrapped.append(p)
            p.append(element)
    return wrapped


def make_ul(soup: BeautifulSoup, elements: List[PageElementOrString]):
    ul = soup.new_tag('ul')
    for element in elements:
        li = soup.new_tag('li')
        li.append(element)
        ul.append(li)
    return ul