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

from bs4 import PageElement, Tag


def closest_common_ancestor(*elements: PageElement) -> Tag:
    if len(elements) < 2:
        raise ValueError("At least two elements are required")

    for parent in elements[0].parents:
        # Standard `in` operator uses value equality `==` for comparison.
        # For two tags this is not satisfying because for example two empty divs
        # will appear equal even if they are in a completely different place in the tree.
        if all(
            any(other_parent is parent for other_parent in element.parents)
            for element in elements[1:]
        ):
            return parent
    raise ValueError("No common parent found")


def is_descendant(child: PageElement, parent: PageElement) -> bool:
    if not isinstance(parent, Tag):
        return False
    for descendant in parent.descendants:
        if child is descendant:
            return True
    return False


def is_parent(parent: PageElement, child: PageElement) -> bool:
    if not isinstance(parent, Tag):
        return False
    for ancestor in child.parents:
        if parent is ancestor:
            return True
    return False
