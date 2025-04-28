from arretify.types import ParsingContext
from .parse_arrete import parse_arrete


def step_segmentation(parsing_context: ParsingContext) -> ParsingContext:
    return parse_arrete(parsing_context)
