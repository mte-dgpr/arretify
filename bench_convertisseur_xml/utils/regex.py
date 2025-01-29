import re
from typing import List, Pattern, cast, List, Callable, Iterable, Union, Dict, Tuple, Literal
from dataclasses import dataclass

from bench_convertisseur_xml.types import PageElementOrString

NAMED_GROUP_PATTERN = re.compile(r'\?P\<(?P<name>\w+)\>')
NAME_WITH_INDEX_PATTERN = re.compile(r'(\w+?)(?P<index>\d+)')

def sub_with_match(string: str, match: re.Match, group: int | str=0) -> str:
    return string[:match.start(group)] + string[match.end(group):]


def without_named_groups(pattern_string: str):
    return NAMED_GROUP_PATTERN.sub('', pattern_string)


def without_named_groups_many(pattern_strings: List[str]):
    return [without_named_groups(pattern_string) for pattern_string in pattern_strings]


def join_with_or(pattern_strings: List[str]):
    return '|'.join(pattern_strings)


def named_groups_indices(pattern_strings: List[str], new_index: int):
    return [ f'({named_groups_index(pattern_s, new_index)})' for pattern_s in pattern_strings ]


def named_groups_index(pattern_string: str, new_index: int):
    remainder = pattern_string
    reconstructed = ''
    while remainder:
        match = NAMED_GROUP_PATTERN.search(remainder)
        if not match:
            break
        reconstructed += remainder[:match.start(0)]
        name = match.group('name')

        name_with_index_match = NAME_WITH_INDEX_PATTERN.search(match.group(0))
        if name_with_index_match:
            name = name_with_index_match.group(1)
        reconstructed += f'?P<{name}{new_index if name_with_index_match else ''}>'
        remainder = remainder[match.end(0):]
    reconstructed += remainder
    return reconstructed


def search_groupdict(re_str: str, date_str: str) -> Dict | None:
    match = re.search(re_str, date_str)
    return match.groupdict() if match else None