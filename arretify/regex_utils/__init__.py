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
from . import regex_tree
from .core import MatchProxy, PatternProxy, safe_group
from .functional import (
    filter_regex_tree_match_children,
    flat_map_regex_tree_match,
    iter_regex_tree_match_page_elements_or_strings,
    map_matches,
    map_regex_tree_match,
)
from .helpers import (
    join_with_or,
    lookup_normalized_version,
    named_group,
    normalize_string,
    remove_accents,
    repeated_with_separator,
    sub_with_match,
    without_named_groups,
)
from .merge import merge_matches_with_siblings
from .split import split_string_with_regex
from .types import Settings
