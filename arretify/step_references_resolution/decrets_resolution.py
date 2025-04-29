from typing import cast
from dataclasses import replace as dataclass_replace
import logging

from bs4 import Tag

from arretify.law_data.uri import parse_uri
from arretify.parsing_utils.dates import parse_date_str
from arretify.types import ParsingContext
from arretify.law_data.apis.legifrance import (
    get_decret_legifrance_id,
)
from arretify.errors import catch_and_log_arretify_error
from .core import (
    update_reference_tag_uri,
    get_title_sample_next_sibling,
)


_LOGGER = logging.getLogger(__name__)


@catch_and_log_arretify_error(_LOGGER)
def resolve_decret_legifrance_id(
    parsing_context: ParsingContext,
    document_reference_tag: Tag,
) -> None:
    uri = cast(str, document_reference_tag.get("data-uri"))
    document, sections = parse_uri(uri)

    if document.date is None:
        raise ValueError(f"Arrete ministeriel document {document} has no date")

    title = get_title_sample_next_sibling(document_reference_tag)
    if title is None and document.num is None:
        _LOGGER.warning(f"Could not resolve decret {document_reference_tag}. No title or num")
        return

    date_object = parse_date_str(document.date)
    decret_id = get_decret_legifrance_id(
        parsing_context,
        date_object,
        title=title,
        num=document.num,
    )
    if decret_id is None:
        _LOGGER.warning(
            f"Could not find legifrance decret id for "
            f'date {date_object}{' n°' + document.num if document.num else ''} "{title}"'
        )
        return

    update_reference_tag_uri(
        document_reference_tag,
        dataclass_replace(
            document,
            id=decret_id,
        ),
        *sections,
    )
