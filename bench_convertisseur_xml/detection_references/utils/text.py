import re
from typing import Pattern, List
import unicodedata


def remove_accents(s: str) -> str:
    return ''.join((c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn'))


def normalize_text(text: str):
    return remove_accents(text.replace('’', "'"))