import re
from typing import Dict, List, Optional, Union

from bs4 import BeautifulSoup, PageElement

from ..types import DataElementSchema, PresentationElementSchema


PageElementOrString = Union[PageElement, str]


def make_element(
    soup: BeautifulSoup, 
    schema: DataElementSchema | PresentationElementSchema, 
    data: Dict[str, str | None]=dict(), 
    contents: List[PageElementOrString] | None=None,
):
    element = soup.new_tag(schema.tag_name)
    if hasattr(schema, 'name'):
        element['class'] = [f'dsr-{schema.name}']
    if hasattr(schema, 'data_keys'):
        for key in schema.data_keys:
            data_value = data[key]
            if data_value is not None:
                element[f'data-{key}'] = data_value
    if contents:
        element.extend(contents)
    return element