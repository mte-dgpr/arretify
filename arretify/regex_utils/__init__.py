#
# Copyright (c) 2025 Direction générale de la prévention des risques (DGPR).
#
# This file is part of Arrêtify.
# See https://github.com/mte-dgpr/arretify for further info.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from .split import split_string_with_regex
from .split_with_regex_tree import split_string_with_regex_tree
from .functional import (
    flat_map_regex_tree_match,
    map_regex_tree_match,
    map_regex_tree_match_strings,
    map_matches,
    iter_regex_tree_match_strings,
    filter_regex_tree_match_children,
)
from .merge import merge_matches_with_siblings
from . import regex_tree
from .core import PatternProxy, MatchProxy, safe_group
from .helpers import (
    sub_with_match,
    without_named_groups,
    join_with_or,
    remove_accents,
    named_group,
    lookup_normalized_version,
    repeated_with_separator,
)
from .types import Settings
