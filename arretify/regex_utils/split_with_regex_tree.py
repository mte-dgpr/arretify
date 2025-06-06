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
