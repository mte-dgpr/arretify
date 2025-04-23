from typing import List

from bs4 import BeautifulSoup

from arretify.html_schemas import (
    ALINEA_SCHEMA,
    DOCUMENT_REFERENCE_SCHEMA,
    OPERATION_SCHEMA,
)
from arretify.types import PageElementOrString
from arretify.utils.html import make_css_class, replace_children

from .operations_detection import (
    parse_operations,
)
from .operands_detection import (
    resolve_references_and_operands,
)


ALINEA_CSS_CLASS = make_css_class(ALINEA_SCHEMA)
DOCUMENT_REFERENCE_CSS_CLASS = make_css_class(DOCUMENT_REFERENCE_SCHEMA)
OPERATION_CSS_CLASS = make_css_class(OPERATION_SCHEMA)


def step_consolidation(soup: BeautifulSoup) -> BeautifulSoup:
    # Find consolidation operations
    for container_tag in soup.select(f".{ALINEA_CSS_CLASS}, .{ALINEA_CSS_CLASS} *"):
        new_children: List[PageElementOrString] = list(container_tag.children)

        document_reference_tags = container_tag.select(f".{DOCUMENT_REFERENCE_CSS_CLASS}")
        if document_reference_tags:
            new_children = parse_operations(soup, new_children)

        replace_children(container_tag, new_children)

    # Resolve operation references and operands
    for operation_tag in soup.select(f".{OPERATION_CSS_CLASS}"):
        resolve_references_and_operands(operation_tag)
    return soup
