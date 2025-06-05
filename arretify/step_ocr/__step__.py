import logging

from arretify.types import ParsingContext
from .mistral_ocr import mistral_ocr


_LOGGER = logging.getLogger(__name__)


def step_ocr(
    parsing_context: ParsingContext,
) -> ParsingContext:
    if not parsing_context.pdf:
        raise ValueError("Parsing context does not contain a PDF file")
    return mistral_ocr(parsing_context)
