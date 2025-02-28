from typing import cast

from .regex_tree.types import GroupNode, RegexTreeMatchFlow
from .regex_tree.execute import match
from .split import split_string_with_regex
from .core import safe_group


def split_string_with_regex_tree(node: GroupNode, string: str) -> RegexTreeMatchFlow:
    for str_or_match in split_string_with_regex(node.pattern, string):
        if isinstance(str_or_match, str):
            yield str_or_match
            continue
        regex_tree_match = match(node, safe_group(str_or_match, 0))
        if not regex_tree_match:
            raise RuntimeError(f"expected '{string}' to match {node.pattern}")
        yield regex_tree_match
