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
    ProtectedSoup,
    ProtectedTag,
    ProtectedTagOrStr,
    protect_tag,
    unprotect_soup,
    unprotect_tag,
)
from arretify.utils.html import is_tag, set_attribute, set_non_data_attributes
from arretify.utils.html_semantic import (
    _SPEC_DATA_ATTR,
    Contents,
    SemanticTagSpec,
    TSemanticTagData,
    get_semantic_tag_spec,
    is_semantic_tag,
    set_semantic_tag_data,
)
from arretify.utils.html_split_merge import group_strings_splitter, merge_strings, recombine_strings
from arretify.utils.split_merge import split_and_map_elements

_TAGS_ALLOWED_ANYWHERE = {"b", "strong", "i", "em", "u", "br"}
"""
These tags are considered as non-structural and can be freely used
throughout the document.
"""


InvalidContentsErrorEntry = tuple[int, str]


class InvalidContentsError(ValueError):
    """
    Raised when the contents of a tag do not conform to the expected structure.
    Attributes:
        errors: A list of tuples where each tuple contains the index of the invalid
                content and a description of the error.
    """

    def __init__(
        self, errors: Sequence[InvalidContentsErrorEntry], prefix: str | None = None
    ) -> None:
        super().__init__(
            (prefix + "\n")
            if prefix
            else "" + "\n".join(f"Index {i}: {message}" for i, message in errors)
        )
        self.errors = errors


def wrap_in_tag(
    soup: ProtectedSoup,
    tag_name: str,
    elements: Sequence[ProtectedTagOrStr],
) -> list[ProtectedTag]:
    wrapped: list[ProtectedTag] = []
    for element in elements:
        if isinstance(element, str) and element.strip():
            container = _make_tag(soup, tag_name)
            wrapped.append(container)
            unprotect_tag(container).append(element)
    return wrapped


def make_tag(
    soup: ProtectedSoup,
    tag_name: str,
    contents: Iterable[ProtectedTagOrStr] | None = None,
    attrs: dict[str, str] | None = None,
) -> ProtectedTag:
    contents = _prepare_contents_for_make_tag(contents)
    tag = _make_tag(soup, tag_name)
    set_non_data_attributes(tag, attrs)
    _validate_tag_contents(contents)
    return _replace_contents(tag, contents)


def make_semantic_tag(
    soup: ProtectedSoup,
    spec: SemanticTagSpec[TSemanticTagData],
    contents: Iterable[ProtectedTagOrStr] | None = None,
    data: TSemanticTagData | None = None,
    attrs: dict[str, str] | None = None,
) -> ProtectedTag:
    contents = _prepare_contents_for_make_tag(contents)
    if data is None:
        data = spec.data_model()

    # Create the HTML tag
    if isinstance(spec.tag_name, str):
        tag = _make_tag(soup, spec.tag_name)
    else:
        tag = spec.tag_name(soup, data)

    tag = upgrade_to_semantic_tag(tag, spec, data)
    set_non_data_attributes(tag, attrs)
    validate_semantic_tag_contents(spec, contents)
    return _replace_contents(tag, contents)


def upgrade_to_semantic_tag(
    protected_tag: ProtectedTag,
    spec: SemanticTagSpec[TSemanticTagData],
    data: TSemanticTagData | None = None,
) -> ProtectedTag:
    validate_semantic_tag_contents(spec, protected_tag.contents)
    set_attribute(protected_tag, _SPEC_DATA_ATTR, spec.spec_name)
    if data is None:
        data = spec.data_model()
    set_semantic_tag_data(spec, protected_tag, data)
    return protected_tag


def replace_contents(
    protected_tag: ProtectedTag,
    contents: Sequence[ProtectedTagOrStr],
) -> ProtectedTag:
    if is_semantic_tag(protected_tag):
        spec = get_semantic_tag_spec(protected_tag)
        validate_semantic_tag_contents(spec, contents)
    else:
        _validate_tag_contents(contents)

    return _replace_contents(protected_tag, contents)


def _prepare_contents_for_make_tag(
    contents: Iterable[ProtectedTagOrStr] | None,
) -> Sequence[ProtectedTagOrStr]:
    if contents is None:
        return []
    # 1. We must be careful not to move elements from one part of the tree to another
    # because that might have unexpected side-effects. For example, if iterating
    # over the children of a tag and moving one of them to a new tag, the list
    # currently being iterated is modified. This is why we work with copies here.
    # 2. Also, if contents is an iterator, we need to convert it to a list to keep
    # the elements.
    else:
        return [copy(element) for element in contents]


def _make_tag(
    soup: ProtectedSoup,
    tag_name: str,
) -> ProtectedTag:
    return protect_tag(unprotect_soup(soup).new_tag(tag_name))


def _replace_contents(
    protected_tag: ProtectedTag,
    contents: Sequence[ProtectedTagOrStr],
) -> ProtectedTag:
    tag = unprotect_tag(protected_tag)
    tag.clear()

    # Also, `contents` must be a list and not an iterator because we're mutating
    # the tree here and might have race conditions provoking unexpected behaviors
    # (e.g. `contents` being an iterator over `tag.children`, but `tag.clear`
    # removing all of them).
    contents = split_and_map_elements(
        # Group consecutive string elements and merge
        # them into a single string to avoid extra spaces.
        recombine_strings(contents),
        group_strings_splitter,
        merge_strings,
    )
    tag.extend(_unprotect_page_elements(contents))
    return protect_tag(tag)


def validate_semantic_tag_contents(
    spec: SemanticTagSpec, contents: Sequence[ProtectedTagOrStr]
) -> None:
    """
    Validates that the contents conform to the allowed contents of the semantic tag spec.
    Raises a single InvalidContentsError containing all validation errors if any are found.
    """
    if spec.allowed_contents is None:
        return  # Any content is allowed

    is_str_accepted = any(isinstance(ac, Contents.Str) for ac in spec.allowed_contents)
    tag_names_accepted = {
        ac.tag_name for ac in spec.allowed_contents if isinstance(ac, Contents.Tag)
    }
    spec_names_accepted = {
        ac.spec_name for ac in spec.allowed_contents if isinstance(ac, Contents.SemanticTag)
    }
    errors: list[InvalidContentsErrorEntry] = []

    for i, element in enumerate(contents):
        if isinstance(element, str):
            if not is_str_accepted:
                errors.append((i, "string content not allowed"))

        elif is_semantic_tag(element):
            element_spec = get_semantic_tag_spec(element)
            if element_spec.is_allowed_anywhere:
                continue

            if element_spec.spec_name not in spec_names_accepted:
                errors.append((i, f"semantic tag {element_spec.spec_name} not allowed"))

        elif is_tag(element):
            tag_name = element.name
            # Allow non-structural tags anywhere, unless the spec forbids all contents.
            if len(spec.allowed_contents) > 0 and tag_name in _TAGS_ALLOWED_ANYWHERE:
                continue

            elif tag_name not in tag_names_accepted:
                errors.append((i, f"tag {tag_name} not allowed"))

            _validate_tag_contents(element.contents)

        else:
            errors.append((i, f"invalid content type {type(element)}"))

    if errors:
        raise InvalidContentsError(
            errors, prefix=f"Invalid contents for semantic tag {spec.spec_name}:"
        )


def _validate_tag_contents(contents: Sequence[ProtectedTagOrStr]) -> None:
    """
    Recursively validates that the contents only contain strings and tags.
    Raises a single InvalidContentsError containing all validation errors if any are found.
    """
    errors: list[InvalidContentsErrorEntry] = []

    for i, element in enumerate(contents):

        if isinstance(element, str):
            continue

        elif is_semantic_tag(element):
            spec = get_semantic_tag_spec(element)
            if spec.is_allowed_anywhere:
                continue
            errors.append((i, f"semantic tag {spec.spec_name} not allowed"))

        elif is_tag(element):
            _validate_tag_contents(element.contents)

        else:
            errors.append((i, f"invalid content type {type(element)}"))

    if errors:
        raise InvalidContentsError(errors, prefix="Invalid contents for tag:")


def _unprotect_page_elements(
    protected_elements: Iterable[ProtectedTagOrStr],
) -> Iterable[PageElement]:
    return cast(Iterable[PageElement], protected_elements)
