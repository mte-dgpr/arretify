from bs4 import BeautifulSoup

from arretify.parsing_utils.source_mapping import (
    TextSegments,
)
from .parse_arrete import parse_arrete


def step_segmentation(lines: TextSegments) -> BeautifulSoup:
    return parse_arrete(lines)
