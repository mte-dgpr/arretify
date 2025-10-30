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
from copy import copy
from typing import Iterable, Sequence, cast

from bs4 import PageElement

from arretify.types import (
    ProtectedTagOrStr,
    ProtectedSoup,
    ProtectedTag,
    protect_tag,
    unprotect_soup,
    unprotect_tag,
)
from arretify.utils.split_merge import (
    split_elements,
    map_splitted_elements,
)
from arretify.utils.html_split_merge import group_strings_splitter
from arretify.utils.strings import (
    merge_strings,
)


def wrap_in_tag(
    soup: ProtectedSoup,
    elements: Sequence[ProtectedTagOrStr],
    tag_name: str,
) -> list[ProtectedTag]:
    wrapped: list[ProtectedTag] = []
    for element in elements:
        if isinstance(element, str) and element.strip():
            container = make_new_tag(soup, tag_name)
            wrapped.append(container)
            unprotect_tag(container).append(element)
    return wrapped


def make_new_tag(
    soup: ProtectedSoup,
    tag_name: str,
    contents: Iterable[ProtectedTagOrStr] | None = None,
) -> ProtectedTag:
    # We must be careful not to move elements from one part of the tree to another
    # because that might have unexpected side-effects.
    # For example, if iterating over the children of a tag and moving one of them
    # to a new tag, the list currently being iterated is modified.
    # This is why we work with copies here.
    cloned_contents: list[ProtectedTagOrStr]
    if contents is None:
        cloned_contents = []
    else:
        cloned_contents = [copy(element) for element in contents]

    element = unprotect_soup(soup).new_tag(tag_name)
    element.extend(
        _unprotect_page_elements(
            map_splitted_elements(
                split_elements(
                    cloned_contents,
                    group_strings_splitter,
                ),
                merge_strings,
            )
        )
    )
    return protect_tag(element)


def replace_children(
    protected_tag: ProtectedTag,
    contents: Sequence[ProtectedTagOrStr],
) -> ProtectedTag:
    tag = unprotect_tag(protected_tag)
    tag.clear()
    # NOTE : `contents` must be a list and not an iterator because
    # we're mutating the tree here and might have race conditions
    # provoking unexpected behaviors (e.g. `contents` being a iterator
    # over `tag.children`, but `tag.clear` removing all of them).
    tag.extend(_unprotect_page_elements(contents))
    return protect_tag(tag)


def _unprotect_page_elements(
    protected_elements: Iterable[ProtectedTagOrStr],
) -> Iterable[PageElement]:
    return cast(Iterable[PageElement], protected_elements)
