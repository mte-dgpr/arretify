"""Regex rules."""

import re
from typing import List

from arretify.utils.html import PageElementOrString
from arretify.regex_utils import (
    PatternProxy,
    join_with_or,
)


VISA_PATTERN = PatternProxy(r"^(vu|-\s*vu)(\s*:\s*|\b)(?P<contents>.*)")
"""Detect if the sentence starts with "vu"."""

MOTIF_PATTERN = PatternProxy(r"^(considérant|-\s*considérant)(\s*:\s*|\b)(?P<contents>.*)")
"""Detect if the sentence starts with "considerant"."""

LIST_PATTERN = PatternProxy(r"^(?P<indentation>\s*)(-\s|[a-zA-Z1-9][\)°]\s+)")
"""Detect if the line starts with - or a number or letter followed by )."""

SENTENCE_WITH_SEMICOLUMN_PATTERN = PatternProxy(r"\S\s*:\s*$")

SERVICES_PATTERNS_LIST = [
    r"préfecture",
    r"sous-préfecture",
    r"secrétariat",
    r"sg",
    r"préfète?",
    r"direction",
    r"drire",
    r"dreal",
    r"service",
    r"section",
    r"pôle",
    r"bureau",
    r"unité",
    r"installations classées pour la protection de l'environnement",  # sometimes independent
    r"réf",
    r"n°",
    r"n/ref",
    r"nor",
]
"""Detect all local authorities taking the arretes."""

SERVICES_PATTERN = PatternProxy(join_with_or(SERVICES_PATTERNS_LIST))

HONORARY_PATTERNS_LIST = [
    r"la préfecture",
    r"l[ea] préfète?",
    r"chevalier",
    r"officier",
    r"commandeur",
]
"""Detect all honorary titles given to the local authorities."""

ENTITY_PATTERN = PatternProxy(
    f"^({join_with_or(SERVICES_PATTERNS_LIST + HONORARY_PATTERNS_LIST)})\\b"
)
"""Detect if starts with local authorities references."""

ARRETE_PATTERN = PatternProxy(r"^[\s-]*(a\s*r\s*r\s*ê\s*t\s*é)[\s-]*\b")

TABLE_DESCRIPTION_PATTERN = PatternProxy(r"^(\(\*+\))|^(\*+)")

BLOCKQUOTE_START_PATTERN = PatternProxy(r"^\s*\"")

BLOCKQUOTE_END_PATTERN = PatternProxy(r"\"[\s\.]*$")

IMAGE_PATTERN = PatternProxy(r"!\[[^\[\]]+\]\([^()]+\)")


def is_line_with_semicolumn(line: str):
    """Detect that sentence is continuing."""
    return bool(SENTENCE_WITH_SEMICOLUMN_PATTERN.search(line))


def is_entity(line: str) -> bool:
    """Detect if the sentence starts with the name of an entity."""
    return bool(ENTITY_PATTERN.match(line))


def is_visa(line: str) -> bool:
    return bool(VISA_PATTERN.match(line))


def is_motif(line: str) -> bool:
    return bool(MOTIF_PATTERN.match(line))


def is_arrete(line: str) -> bool:
    """Detect if the sentence starts with "arrete"."""
    return bool(ARRETE_PATTERN.match(line))


def is_liste(line: str) -> bool:
    return bool(LIST_PATTERN.match(line))


def is_table_description(line: str, pile: List[PageElementOrString]) -> bool:
    # Sentence starts with any number of * between parentheses or without parentheses
    match = TABLE_DESCRIPTION_PATTERN.search(line)
    if match:
        return True

    # Sentence that explains the name of one of the columns
    pile_bottom = pile[0] if len(pile) >= 1 else None
    if isinstance(pile_bottom, str):
        column_names = []
        columns_split = pile_bottom.split("|")
        for column_split in columns_split:
            column_strip = column_split.strip()
            column_raw = re.sub(r"\([^)]*\)", "", column_strip).strip()
            if len(column_raw) > 0:
                column_names.append(column_raw)

        # For each column name, check if we have it followed by :
        for column_name in column_names:
            if re.match(rf".*{re.escape(column_name)} :", line, re.IGNORECASE):
                return True
    return False


def is_blockquote_start(line: str) -> bool:
    return bool(BLOCKQUOTE_START_PATTERN.search(line))


def is_blockquote_end(line: str) -> bool:
    return bool(BLOCKQUOTE_END_PATTERN.search(line))


def is_image(line: str) -> bool:
    return bool(IMAGE_PATTERN.search(line))
