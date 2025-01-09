import re
from typing import Dict, List, Optional, Union

from bs4 import BeautifulSoup, PageElement, Tag

from ..types import DataElementSchema, PageElementOrString


def make_css_class(schema: DataElementSchema):
    return f'dsr-{schema.name}'


def make_data_tag(
    soup: BeautifulSoup, 
    schema: DataElementSchema, 
    contents: List[PageElementOrString]=[],
    data: Dict[str, str | None]=dict(), 
) -> Tag:
    element = make_new_tag(soup, schema.tag_name, contents=contents)
    element['class'] = [make_css_class(schema)]
    for key in schema.data_keys:
        data_value = data[key]
        if data_value is not None:
            element[f'data-{key}'] = data_value
    return element


def wrap_in_tag(soup: BeautifulSoup, elements: List[PageElementOrString], tag_name: str):
    wrapped: List[Tag] = []
    for element in elements:
        if isinstance(element, str) and element.strip():
            container = soup.new_tag(tag_name)
            wrapped.append(container)
            container.append(element)
    return wrapped


def make_ul(soup: BeautifulSoup, elements: List[PageElementOrString]):
    ul = soup.new_tag('ul')
    for element in elements:
        if isinstance(element, Tag) and element.name == 'li':
            li = element
        else:
            li = make_li(soup, [element])
        ul.append(li)
    return ul


def make_li(soup: BeautifulSoup, elements: List[PageElementOrString]):
    li = soup.new_tag('li')
    li.extend(elements)
    return li


def make_new_tag(soup: BeautifulSoup, tag_name: str, contents: List[PageElementOrString] = []):
    element = soup.new_tag(tag_name)
    element.extend(contents)
    return element