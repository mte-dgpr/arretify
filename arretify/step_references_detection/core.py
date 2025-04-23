from typing import Iterable, List

from bs4 import Tag

from arretify.types import PageElementOrString
from arretify.utils.html import make_css_class
from arretify.html_schemas import SECTION_REFERENCE_SCHEMA


SECTION_REFERENCE_CSS_CLASS = make_css_class(SECTION_REFERENCE_SCHEMA)


def filter_section_references(
    children: Iterable[PageElementOrString],
) -> List[Tag]:
    return [
        child
        for child in children
        if (isinstance(child, Tag) and SECTION_REFERENCE_CSS_CLASS in child.get("class", []))
    ]
