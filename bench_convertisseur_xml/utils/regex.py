import re
from typing import List, Pattern, cast, List, Callable, Iterable, Union, Dict, Tuple, Literal
from dataclasses import dataclass

from bench_convertisseur_xml.types import PageElementOrString

NAMED_GROUP_RE = re.compile(r'\?P\<\w+\>')


def sub_with_match(string: str, match: re.Match, group: int | str=0) -> str:
    return string[:match.start(group)] + string[match.end(group):]


def without_named_groups(pattern_string: str):
    return NAMED_GROUP_RE.sub('', pattern_string)
