from .types import (
    Node,
    RegexTreeMatch,
    LiteralNode,
    BranchingNode,
    QuantifierNode,
    GroupNode,
    SequenceNode,
    RegexTreeMatchFlow,
)
from ..split import (
    split_string_with_regex,
    split_match_by_named_groups,
)
from ..core import safe_group


def match(node: GroupNode, string: str) -> RegexTreeMatch | None:
    try:
        results = list(_match_recursive(node, string, None))
    except NoMatch:
        return None

    if len(results) != 1 or not isinstance(results[0], RegexTreeMatch):
        raise RuntimeError(f"expected exactly one match group, got {results}")
    else:
        return results[0]


def _match_recursive(
    node: Node,
    string: str,
    current_group: RegexTreeMatch | None,
) -> RegexTreeMatchFlow:
    # For BranchingNode, we can't use `pattern` to match the string,
    # we have to try each child until we find a match.
    if isinstance(node, BranchingNode):
        for child in node.children.values():
            try:
                children_results = list(_match_recursive(child, string, current_group))
            except NoMatch:
                continue
            # Yield and return on first match
            yield from children_results
            return
        else:
            raise NoMatch()

    elif isinstance(node, GroupNode):
        child_group = RegexTreeMatch(
            children=[],
            group_name=node.group_name,
            match_dict=dict(),
        )
        child_group.children.extend(_match_recursive(node.child, string, child_group))
        yield child_group
        return

    # For other nodes, there is no problem using `pattern`.
    match = node.pattern.match(string)
    if not match:
        raise NoMatch()
    if not current_group:
        raise RuntimeError("current_group should not be None")

    if isinstance(node, LiteralNode):
        # Remove None values from the match_dict
        current_group.match_dict.update(
            {k: v for k, v in match.groupdict().items() if v is not None}
        )
        yield safe_group(match, 0)
        return

    elif isinstance(node, QuantifierNode):
        for str_or_match in split_string_with_regex(node.child.pattern, safe_group(match, 0)):
            if isinstance(str_or_match, str):
                yield str_or_match
                continue
            yield from _match_recursive(node.child, safe_group(str_or_match, 0), current_group)

    elif isinstance(node, SequenceNode):
        for str_or_group in split_match_by_named_groups(match):
            if isinstance(str_or_group, str):
                yield str_or_group
                continue
            child = node.children[str_or_group.group_name]
            yield from _match_recursive(child, str_or_group.text, current_group)

    else:
        raise RuntimeError(f"unexpected node type: {node}")


class NoMatch(Exception):
    """
    Enables the algorithm to break out of the current branch and try the next one.
    """
