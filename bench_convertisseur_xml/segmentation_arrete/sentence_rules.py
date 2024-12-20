"""Regex rules."""


import re
from typing import List

from bench_convertisseur_xml.utils.text import remove_accents
from bench_convertisseur_xml.utils.html import PageElementOrString
from .config import HONORARY_PATTERNS, SERVICE_PATTERNS, BodySection


def is_line_with_semicolumn(line: str):
    """Detect that sentence is continuing."""
    return bool(re.search(r"\S\s*:\s*$", line))


def is_entity(line: str) -> bool:
    """Detect if the sentence starts with the name of an entity."""

    patterns_to_catch = SERVICE_PATTERNS + HONORARY_PATTERNS
    pattern = f"^({'|'.join(patterns_to_catch)})\\b"

    search_result = bool(re.match(pattern, line, re.IGNORECASE))

    return search_result


def is_visa(line: str) -> bool:
    """Detect if the sentence starts with "vu"."""
    search_result = bool(re.match(r"^(vu|-\svu)\b", line, re.IGNORECASE))
    return search_result


def is_motif(line: str) -> bool:
    """Detect if the sentence starts with "considerant"."""
    return bool(re.match(r"^(consid[eé]rant|-\sconsid[eé]rant)\b", line, re.IGNORECASE))


def is_arrete(line: str) -> bool:
    """Detect if the sentence starts with "arrete"."""
    return bool(re.match(r"^(arr[eéê]t[eé])\b", line, re.IGNORECASE))


def is_liste(line: str) -> bool:
    """Detect if the line starts with - or a number or letter followed by )."""
    search_result = bool(re.match(r"^(-\s|[a-zA-Z1-9][\)°]\s+)", line, re.IGNORECASE))
    return search_result


def is_table_description(line: str, pile: List[PageElementOrString]) -> bool:
    # Sentence starts with any number of * between parentheses or without parentheses
    match = re.search(r"^(\(\*+\))|^(\*+)", line, re.IGNORECASE)
    if match:
        return True

    # Sentence that explains the name of one of the columns
    pile_bottom = pile[0] if len(pile) >= 1 else None
    if isinstance(pile_bottom, str):
        column_names = []
        columns_split = pile_bottom.split("|")
        for column_split in columns_split:
            column_strip = column_split.strip()
            column_raw = re.sub(r"\([^)]*\)", '', column_strip).strip()
            if len(column_raw) > 0:
                column_names.append(column_raw)

        # For each column name, check if we have it followed by :
        for column_name in column_names:
            if re.match(fr".*{re.escape(column_name)} :", line, re.IGNORECASE):
                return True
    return False


def is_table(line: str) -> bool:
    """Detect if the line is part of a table."""
    # Any | character to detect a table
    return bool(re.search(r"(\|)", line, re.IGNORECASE))
