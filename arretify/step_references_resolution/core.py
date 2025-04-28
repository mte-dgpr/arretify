from typing import cast, Callable

from bs4 import Tag
from arretify._vendor.clients_api_droit.clients_api_droit.legifrance import (
    build_jorf_url,
    build_code_site_url,
    build_code_article_site_url,
)

from arretify.regex_utils import (
    PatternProxy,
    safe_group,
)
from arretify.html_schemas import (
    SECTION_REFERENCE_SCHEMA,
    DOCUMENT_REFERENCE_SCHEMA,
)
from arretify.law_data.types import (
    Document,
    DocumentType,
    Section,
    SectionType,
)
from arretify.law_data.uri import (
    is_uri_document_type,
    is_resolvable,
    render_uri,
)
from arretify.utils.html import (
    make_css_class,
    render_bool_attribute,
)
from arretify.types import ExternalURL, ParsingContext


SECTION_REFERENCE_CSS_CLASS = make_css_class(SECTION_REFERENCE_SCHEMA)
DOCUMENT_REFERENCE_CSS_CLASS = make_css_class(DOCUMENT_REFERENCE_SCHEMA)
# Regex for searching an act with its title.
# Simply picks the first 3 to 15 words following the document reference.
TITLE_SAMPLE_PATTERN = PatternProxy(r"^\s*([^\.;\s]+\s+){3,15}([^\.;\s]+)")


ReferenceResolutionFunction = Callable[[ParsingContext, Tag], None]


def resolve_external_url(
    document: Document,
    *sections: Section,
) -> ExternalURL | None:
    if document.type in [
        DocumentType.arrete_ministeriel,
        DocumentType.decret,
        DocumentType.circulaire,
    ]:
        if document.id is not None:
            return build_jorf_url(document.id)

    elif document.type == DocumentType.code:
        if document.id is None:
            return None

        elif (
            sections
            and sections[0].type == SectionType.article
            and sections[0].start_id is not None
        ):
            return build_code_article_site_url(sections[0].start_id)

        else:
            return build_code_site_url(document.id)

    elif document.type in [
        DocumentType.eu_decision,
        DocumentType.eu_regulation,
        DocumentType.eu_directive,
    ]:
        return document.id

    return None


def resolve_document_references(
    parsing_context: ParsingContext,
    document_type: DocumentType,
    reference_resolution_function: ReferenceResolutionFunction,
):
    filter_function = _make_reference_filter(document_type, DOCUMENT_REFERENCE_CSS_CLASS)
    for document_reference_tag in parsing_context.soup.find_all(filter_function):
        reference_resolution_function(parsing_context, document_reference_tag)


def resolve_section_references(
    parsing_context: ParsingContext,
    document_type: DocumentType,
    reference_resolution_function: ReferenceResolutionFunction,
):
    filter_function = _make_reference_filter(document_type, SECTION_REFERENCE_CSS_CLASS)
    for section_reference_tag in parsing_context.soup.find_all(filter_function):
        reference_resolution_function(parsing_context, section_reference_tag)


def update_reference_tag_uri(tag: Tag, document: Document, *sections: Section) -> None:
    is_document_resolvable = is_resolvable(document, *sections)
    updated_uri = render_uri(document, *sections)
    tag["data-uri"] = updated_uri
    tag["data-is_resolvable"] = render_bool_attribute(is_document_resolvable)

    if is_document_resolvable:
        external_url = resolve_external_url(document, *sections)
        if external_url is None:
            raise ValueError(f"Could not resolve external url for {document}")
        tag["href"] = external_url


def get_title_sample_next_sibling(
    document_reference_tag: Tag,
) -> str | None:
    title_element = document_reference_tag.next_sibling
    if title_element is None or not isinstance(title_element, str):
        return None

    match = TITLE_SAMPLE_PATTERN.match(title_element)
    if match:
        return safe_group(match, 0)
    return None


def _make_reference_filter(
    document_type: DocumentType,
    css_class: str,
) -> Callable[[Tag], bool]:
    def _filter_function(tag: Tag) -> bool:
        return css_class in tag.get("class", []) and is_uri_document_type(
            cast(str, tag.get("data-uri", "")), document_type
        )

    return _filter_function
