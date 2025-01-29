"""
Custom regex engine package. It provides the following features:
- Nested regex definitions, providing encapsulation and modularity
- Ability to have multiple times the same named group in a regex
- Functions to iterate the results of a regex match and recover the named groups
"""

from .compile import Group, Branching, Sequence, Leaf, Quantifier, Node
from .execute import split_string
from .functional import flat_map_match_group
from .types import MatchGroup, MatchDict