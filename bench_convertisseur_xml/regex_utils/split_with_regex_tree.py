from .regex_tree.types import GroupNode, RegexTreeMatchFlow
from .regex_tree.execute import match
from .split import split_string_with_regex


def split_string_with_regex_tree(node: GroupNode, string: str) -> RegexTreeMatchFlow:
    accumulator = ""
    for str_or_match in split_string_with_regex(node.pattern, string):
        if isinstance(str_or_match, str):
            accumulator += str_or_match
            continue

        # It can happen that the regex matches the node.pattern, 
        # but the regex_tree match fails because for example of a nested 
        # node with different settings (e.g. ignore_case = False).
        regex_tree_match = match(node, str_or_match.group(0))
        if regex_tree_match is None:
            accumulator += str_or_match.group(0)
            continue

        if accumulator:
            yield accumulator
            accumulator = ""
        yield regex_tree_match

    if accumulator:
        yield accumulator
