from typing import List


from arretify.types import PageElementOrString, ParsingContext
from arretify.utils.html import make_css_class, replace_children
from arretify.html_schemas import (
    ALINEA_SCHEMA,
    MOTIF_SCHEMA,
    VISA_SCHEMA,
)

from .sections_detection import (
    parse_section_references,
)
from .arretes_detection import (
    parse_arretes_references,
)
from .decrets_detection import (
    parse_decrets_references,
)
from .circulaires_detection import (
    parse_circulaires_references,
)
from .codes_detection import (
    parse_codes_references,
)
from .self_detection import parse_self_references
from .eu_acts_detection import (
    parse_eu_acts_references,
)
from .match_sections_with_documents import match_sections_with_documents


ALINEA_CSS_CLASS = make_css_class(ALINEA_SCHEMA)
MOTIF_CSS_CLASS = make_css_class(MOTIF_SCHEMA)
VISA_CSS_CLASS = make_css_class(VISA_SCHEMA)


def step_references_detection(parsing_context: ParsingContext) -> ParsingContext:
    new_children: List[PageElementOrString]

    # Parse documents and sections references
    for tag in parsing_context.soup.select(
        f".{ALINEA_CSS_CLASS}, .{ALINEA_CSS_CLASS} *, .{MOTIF_CSS_CLASS}, .{VISA_CSS_CLASS}"
    ):
        new_children = list(tag.children)
        new_children = parse_arretes_references(parsing_context, new_children)
        new_children = parse_decrets_references(parsing_context, new_children)
        new_children = parse_circulaires_references(parsing_context, new_children)
        new_children = parse_codes_references(parsing_context, new_children)
        new_children = parse_self_references(parsing_context, new_children)
        new_children = parse_eu_acts_references(parsing_context, new_children)
        new_children = parse_section_references(parsing_context, new_children)
        replace_children(tag, new_children)

    # Match sections with documents
    for tag in parsing_context.soup.select(
        f".{ALINEA_CSS_CLASS}, .{ALINEA_CSS_CLASS} *, .{MOTIF_CSS_CLASS}, .{VISA_CSS_CLASS}"
    ):
        new_children = list(tag.children)
        new_children = match_sections_with_documents(parsing_context, new_children)
        replace_children(tag, new_children)

    return parsing_context
