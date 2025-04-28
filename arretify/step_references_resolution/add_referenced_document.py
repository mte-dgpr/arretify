# TODO : this is a temporary solution, but eventually we need to
# refactor the URI system which is not really adapted to the new
# way of referencing documents from sections.

from typing import cast

from arretify.types import ParsingContext
from arretify.utils.html import make_css_class, render_bool_attribute
from arretify.html_schemas import SECTION_REFERENCE_SCHEMA, DOCUMENT_REFERENCE_SCHEMA
from arretify.law_data.uri import parse_uri, render_uri, is_resolvable


SECTION_REFERENCE_CSS_CLASS = make_css_class(SECTION_REFERENCE_SCHEMA)
DOCUMENT_REFERENCE_CSS_CLASS = make_css_class(DOCUMENT_REFERENCE_SCHEMA)


def add_referenced_document_DEPRECATED(
    parsing_context: ParsingContext,
) -> None:

    for section_reference_tag in parsing_context.soup.select(f".{SECTION_REFERENCE_CSS_CLASS}"):
        document_reference_element_id = section_reference_tag.get("data-document_reference")
        if not document_reference_element_id:
            continue

        # Get the document reference tag
        document_reference_tag = parsing_context.soup.select_one(
            f'.{DOCUMENT_REFERENCE_CSS_CLASS}[data-element_id="{document_reference_element_id}"]'
        )
        if not document_reference_tag:
            raise ValueError(
                f"Document reference tag with id {document_reference_element_id} not found"
            )

        document, _ = parse_uri(cast(str, document_reference_tag["data-uri"]))
        _, sections = parse_uri(cast(str, section_reference_tag["data-uri"]))

        section_reference_tag["data-uri"] = render_uri(document, *sections)
        section_reference_tag["data-is_resolvable"] = render_bool_attribute(
            is_resolvable(document, *sections)
        )
