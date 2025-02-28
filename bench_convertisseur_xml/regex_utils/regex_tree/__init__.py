"""
Custom regex tree package. It provides the following features:
- Nested regex definitions, providing encapsulation and modularity
- Ability to have multiple times the same named group in a regex
- Possibility to iterate the results of a regex match and recover the named groups
"""

from .compile import Group, Branching, Sequence, Literal, Quantifier, Node
from .execute import match
from .types import RegexTreeMatch as Match, GroupNode, MatchDict