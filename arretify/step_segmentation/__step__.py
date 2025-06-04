from arretify.types import ParsingContext
from .parse_arrete import parse_arrete


def step_segmentation(parsing_context: ParsingContext) -> ParsingContext:
    if not parsing_context.lines:
        raise ValueError("Parsing context does not contain any lines to segment")
    return parse_arrete(parsing_context)
