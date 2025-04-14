from typing import cast
from dataclasses import replace as dataclass_replace

from bs4 import Tag

from bench_convertisseur_xml.settings import LOGGER
from bench_convertisseur_xml.law_data.uri import (
    parse_uri,
)
from bench_convertisseur_xml.law_data.eurlex import (
    get_eu_act_url_with_year_and_num,
    ActType,
)
from .core import update_reference_tag_uri


def resolve_eu_decision_eurlex_url(
    eu_act_reference_tag: Tag,
) -> None:
    return _resolve_eu_act_eurlex_url("decision", eu_act_reference_tag)


def resolve_eu_regulation_eurlex_url(
    eu_act_reference_tag: Tag,
) -> None:
    return _resolve_eu_act_eurlex_url("regulation", eu_act_reference_tag)


def resolve_eu_directive_eurlex_url(
    eu_act_reference_tag: Tag,
) -> None:
    return _resolve_eu_act_eurlex_url("directive", eu_act_reference_tag)


def _resolve_eu_act_eurlex_url(
    act_type: ActType,
    eu_act_reference_tag: Tag,
) -> None:
    document, sections = parse_uri(cast(str, eu_act_reference_tag["data-uri"]))

    if document.num is None or document.date is None:
        raise ValueError(f"Could not find num or date for document {document}")

    eurlex_url = get_eu_act_url_with_year_and_num(act_type, int(document.date), int(document.num))
    if eurlex_url is None:
        LOGGER.warning(f"Could not find eurlex url for {act_type} {document.date}/{document.num}")
        return

    update_reference_tag_uri(
        eu_act_reference_tag,
        dataclass_replace(document, id=eurlex_url),
        *sections,
    )
