import re
from typing import Dict, List, Optional, Union

from bs4 import BeautifulSoup, PageElement

from ..types import ElementSchema


PageElementOrString = Union[PageElement, str]


def make_element(
    soup: BeautifulSoup, 
    schema: ElementSchema, 
    data: Dict[str, str | None]=dict(), 
    contents: List[PageElementOrString] | None=None,
):
    element = soup.new_tag(schema.tag_name)
    element['class'] = []
    element['class'].extend(schema.classes)
    for key in schema.data_keys:
        if data[key] is not None:
            element[f'data-{key}'] = data[key]
    if contents:
        element.extend(contents)
    return element