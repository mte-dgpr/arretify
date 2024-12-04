import re
from typing import Pattern, List
import unicodedata


def remove_accents(s: str) -> str:
    return ''.join((c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn'))


def normalize_text(regex: Pattern, text: str, placeholder: str):
    remainder: str = remove_accents(text.replace('’', "'"))
    matches: List[re.Match] = []
    while True:
        match = regex.search(remainder)
        if not match:
            break
        matches.append(match)
        remainder = remainder[:match.start()] + placeholder + remainder[match.end():]
    return matches, remainder
