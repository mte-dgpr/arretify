import re
import unicodedata
from typing import List, Pattern, cast, List, Callable, Iterable, Union, Dict, Tuple, Literal
from dataclasses import dataclass

from bench_convertisseur_xml.types import PageElementOrString

NAMED_GROUP_PATTERN = re.compile(r'\?P\<(?P<name>\w+)\>')
NAME_WITH_INDEX_PATTERN = re.compile(r'(\w+?)(?P<index>\d+)')


def sub_with_match(string: str, match: re.Match, group: int | str=0) -> str:
    return string[:match.start(group)] + string[match.end(group):]


def without_named_groups(pattern_string: str):
    return NAMED_GROUP_PATTERN.sub('', pattern_string)


def join_with_or(pattern_strings: List[str]):
    return '|'.join(pattern_strings)


def remove_accents(s: str) -> str:
    return ''.join((c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn'))


def normalize_quotes(text: str):
    return (text
        .replace('’', "'")
        .replace('“', '"')
        .replace('”', '"')
        .replace('«', '"')
        .replace('»', '"'))