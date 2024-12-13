"""Regex rules."""


import re
from typing import List

from .config import BodySection


def is_not_information(line: str) -> bool:

    patterns_to_ignore = [
        # Sentence starting with "```"
        r'^```',
        # Sentence starting with "---"
        r'^---',
        # Empty sentence or full of whitespaces
        r'^\s*$',
        # Sentence starting with "!"
        r'^!',

        # Bottom-page with format "X/YY"
        r'^\d+/\d+\s*$',
        # Bottom-page with format "Page X/YY"
        r'^page\s+\d+/\d+\s*$',
        # Bottom-page with format "Page X sur YY"
        r'^page\s+\d+\s+sur\s+\d+\s*$',
        # Bottom-page with format "Page X"
        r'^page\s+\d+$',

        # Sentence starting with "sur"
        r'^sur\b',
        # Sentence starting with "apres"
        r'^apr[eè]s\b',

        # French Republic
        r"r[eé]publique fran[cç]aise",
        # French national motto
        r"(libert[eé]|[eé]galit[eé]|fraternit[eé])",
        # Phone numbers
        r'\d{2}[\s.]\d{2}[\s.]\d{2}[\s.]\d{2}[\s.]\d{2}'
    ]
    pattern = '|'.join(f'(?:{pattern})' for pattern in patterns_to_ignore)

    search_result = bool(re.search(pattern, line, re.IGNORECASE))

    return search_result


def is_continuing_sentence(line: str) -> bool:
    """Detect sentence starting wit lowercase character."""
    search_result = bool(re.match(r"^[a-z]", line))
    return search_result


def is_entity(line: str) -> bool:
    """Detect if the sentence starts with the name of an entity."""

    patterns_to_catch = [
        r"la pr[ée]fecture",
        r"pr[eé]fecture",
        r"direction",
        r"service",
        r"bureau",
        r"l[ea] pr[ée]f[eè]t",
        r"pr[ée]f[eè]t",
        r"chevalier",
        r"officier",
        r"commandeur",
    ]
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


def is_table_description(line: str, pile: List[str]) -> bool:
    # Second possibility: this sentence explains the name of one of the columns
    if len(pile) >= 1:
        column_names = []
        columns_split = pile[0].split("|")
        for column_split in columns_split:
            column_strip = column_split.strip()
            column_raw = re.sub(r"\([^)]*\)", '', column_strip).strip()
            if len(column_raw) > 0:
                column_names.append(column_raw)

        # For each column name, check if we have it followed by :
        for column_name in column_names:
            if re.match(fr".*{column_name} :", line, re.IGNORECASE):
                return True
    return False


def is_table(line: str) -> bool:
    """Detect if the line is part of a table."""
    # First possibility: any | or sentence starts with any number of * between parentheses
    table_from_starting_element = bool(re.search(r"(\|)|^(\(\*+\))|^(\*+)", line, re.IGNORECASE))
    search_result = table_from_starting_element
    return search_result
