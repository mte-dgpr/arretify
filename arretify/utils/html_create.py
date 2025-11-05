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
from arretify.utils.html import is_tag, set_attribute
from arretify.utils.html_semantic import (
    _SPEC_DATA_ATTR,
    Contents,
    SemanticTagSpec,
    TSemanticTagData,
    get_semantic_tag_spec,
    is_semantic_tag,
    set_semantic_tag_data,
)
from arretify.utils.split_merge import (
    split_elements,
    map_splitted_elements,
)
from arretify.utils.html_split_merge import group_strings_splitter
from arretify.utils.strings import (
    merge_strings,
)


_TAGS_ALLOWED_ANYWHERE = {"b", "strong", "i", "em", "u", "br"}
"""
These tags are considered as non-structural and can be freely used
throughout the document.
"""


def wrap_in_tag(
    soup: ProtectedSoup,
    tag_name: str,
    elements: Sequence[ProtectedTagOrStr],
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
    attrs: dict[str, str] | None = None,
) -> ProtectedTag:
    if contents is None:
        contents = []
    # If contents is an iterator, convert it to a list to keep the elements
    else:
        contents = list(contents)
    _validate_tag_contents(contents)
    return _make_new_tag(soup, tag_name, contents=contents, attrs=attrs)


def make_semantic_tag(
    soup: ProtectedSoup,
    spec: SemanticTagSpec[TSemanticTagData],
    contents: Iterable[ProtectedTagOrStr] | None = None,
    data: TSemanticTagData | None = None,
    attrs: dict[str, str] | None = None,
) -> ProtectedTag:
    if contents is None:
        contents = []
    # If contents is an iterator, convert it to a list to keep the elements
    else:
        contents = list(contents)

    # Create the HTML tag
    tag = _make_new_tag(soup, spec.tag_name, contents=contents, attrs=attrs)

    return upgrade_to_semantic_tag(tag, spec, data)


def upgrade_to_semantic_tag(
    protected_tag: ProtectedTag,
    spec: SemanticTagSpec[TSemanticTagData],
    data: TSemanticTagData | None = None,
) -> ProtectedTag:
    _validate_semantic_tag_contents(spec, protected_tag.contents)
    set_attribute(protected_tag, _SPEC_DATA_ATTR, spec.spec_name)
    if data is None:
        data = spec.data_model()
    set_semantic_tag_data(spec, protected_tag, data)
    return protected_tag


def _make_new_tag(
    soup: ProtectedSoup,
    tag_name: str,
    contents: Iterable[ProtectedTagOrStr],
    attrs: dict[str, str] | None = None,
) -> ProtectedTag:
    # We must be careful not to move elements from one part of the tree to another
    # because that might have unexpected side-effects.
    # For example, if iterating over the children of a tag and moving one of them
    # to a new tag, the list currently being iterated is modified.
    # This is why we work with copies here.
    cloned_contents: list[ProtectedTagOrStr] = [copy(element) for element in contents]

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

    if attrs:
        for key, value in attrs.items():
            if key.startswith("data-"):
                raise ValueError("Attribute data-* are reserved for semantic tag data")
            element[key] = value

    return protect_tag(element)


def replace_children(
    protected_tag: ProtectedTag,
    contents: Sequence[ProtectedTagOrStr],
) -> ProtectedTag:
    if is_semantic_tag(protected_tag):
        spec = get_semantic_tag_spec(protected_tag)
        _validate_semantic_tag_contents(spec, contents)
    else:
        _validate_tag_contents(contents)

    tag = unprotect_tag(protected_tag)
    tag.clear()
    # NOTE : `contents` must be a list and not an iterator because
    # we're mutating the tree here and might have race conditions
    # provoking unexpected behaviors (e.g. `contents` being a iterator
    # over `tag.children`, but `tag.clear` removing all of them).
    tag.extend(_unprotect_page_elements(contents))
    return protect_tag(tag)


class InvalidContentsError(ValueError):
    pass


def _validate_semantic_tag_contents(
    spec: SemanticTagSpec, contents: Sequence[ProtectedTagOrStr]
) -> None:
    is_str_accepted = any(isinstance(ac, Contents.Str) for ac in spec.allowed_contents)
    tag_names_accepted = {
        ac.tag_name for ac in spec.allowed_contents if isinstance(ac, Contents.Tag)
    }
    spec_names_accepted = {
        ac.spec_name for ac in spec.allowed_contents if isinstance(ac, Contents.SemanticTag)
    }

    for element in contents:
        if isinstance(element, str):
            if not is_str_accepted:
                raise InvalidContentsError(f"String content not accepted in {spec.spec_name}")

        elif is_semantic_tag(element):
            element_spec = get_semantic_tag_spec(element)
            if element_spec.is_allowed_anywhere:
                continue

            if element_spec.spec_name not in spec_names_accepted:
                raise InvalidContentsError(
                    f'Semantic tag "{element_spec.spec_name}" not accepted in "{spec.spec_name}"'
                )

        elif is_tag(element):
            tag_name = element.name
            # Allow non-structural tags anywhere, unless the spec forbids all contents.
            if len(spec.allowed_contents) > 0 and tag_name in _TAGS_ALLOWED_ANYWHERE:
                continue

            elif tag_name not in tag_names_accepted:
                raise InvalidContentsError(f"Tag <{tag_name}> not accepted in {spec.spec_name}")

            _validate_tag_contents(element.contents)

        else:
            raise InvalidContentsError(f"Invalid content type {type(element)} in {spec.spec_name}")


def _validate_tag_contents(contents: Sequence[ProtectedTagOrStr]) -> None:
    """
    Recursively validates that there is no semantic tag in the subtree.
    """
    for element in contents:
        if is_semantic_tag(element):
            spec = get_semantic_tag_spec(element)
            if spec.is_allowed_anywhere:
                continue

            raise InvalidContentsError(f"Semantic tag {spec.spec_name} not allowed here")

        elif is_tag(element):
            _validate_tag_contents(element.contents)


def _unprotect_page_elements(
    protected_elements: Iterable[ProtectedTagOrStr],
) -> Iterable[PageElement]:
    return cast(Iterable[PageElement], protected_elements)
