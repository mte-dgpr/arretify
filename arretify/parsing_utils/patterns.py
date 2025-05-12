from arretify.regex_utils import PatternProxy


ET_VIRGULE_PATTERN_S = r"(\s*(,|,?et)\s*)"

LEADING_TRAILING_PUNCTUATION_PATTERN = PatternProxy(r"^[\s.]+|[\s.]+$")
"""Detect leading and trailing points or whitespaces."""

LETTER_PATTERN_S = r"[a-zA-Z]"
