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
from typing import Iterable, Iterator, Literal, Sequence, TypeGuard, cast

from bs4 import Tag

from arretify.types import (
    IdCounters,
    ProtectedTag,
    ProtectedTagOrStr,
    TagGroupId,
    TagId,
    protect_tag,
    unprotect_tag,
)
from arretify.utils.functional import iter_func_to_list

INLINE_TAG_TYPES = ["br"]

TAG_ID_ATTR = "data-tag_id"
GROUP_ID_ATTR = "data-group_id"

RESERVED_ATTRS = [TAG_ID_ATTR, GROUP_ID_ATTR]


def is_tag(
    tag: ProtectedTagOrStr,
    tag_name_in: Sequence[str] | None = None,
) -> TypeGuard[ProtectedTag]:
    """
    Check if element is a tag.

    Optionally this function checks also that tag name is included
    in the given `tag_name_in` list.
    """
    if not isinstance(tag, Tag):
        return False

    if tag_name_in is not None:
        if tag.name not in tag_name_in:
            return False

    return True


@iter_func_to_list
def filter_out_inline_tags(
    elements: Iterable[ProtectedTagOrStr],
) -> Iterator[ProtectedTagOrStr]:
    for element in elements:
        if not is_tag(element, tag_name_in=INLINE_TAG_TYPES):
            yield element


def ensure_tag_id(id_counters: IdCounters, tag: ProtectedTag) -> TagId:
    current_tag_id = tag.get(TAG_ID_ATTR, None)
    if current_tag_id is None:
        unprotect_tag(tag)[TAG_ID_ATTR] = _make_id(id_counters, "tag_id")
    return cast(str, tag[TAG_ID_ATTR])


def make_group_id(id_counters: IdCounters) -> TagGroupId:
    return _make_id(id_counters, "group_id")


def set_group_id(tag: ProtectedTag, group_id: TagGroupId) -> TagGroupId:
    current_group_id = tag.get(GROUP_ID_ATTR, None)
    if current_group_id is not None and current_group_id != group_id:
        raise ValueError(f"Tag already has a different group_id: {current_group_id}")
    unprotect_tag(tag)[GROUP_ID_ATTR] = group_id
    return group_id


def set_attribute(
    tag: ProtectedTag,
    attr_name: str,
    attr_value: str,
) -> ProtectedTag:
    if attr_name in RESERVED_ATTRS:
        raise ValueError(f"Cannot set reserved attribute '{attr_name}' using this function")
    return _set_attribute(tag, attr_name, attr_value)


def _set_attribute(
    tag: ProtectedTag,
    attr_name: str,
    attr_value: str,
) -> ProtectedTag:
    unprotect_tag(tag)[attr_name] = attr_value
    return tag


def set_non_data_attributes(
    tag: ProtectedTag,
    attrs: dict[str, str] | None,
) -> ProtectedTag:
    unprotected_tag = unprotect_tag(tag)
    if attrs:
        for key, value in attrs.items():
            if key.startswith("data-"):
                raise ValueError("Attribute data-* are reserved for semantic tag data")
            unprotected_tag[key] = value
    return protect_tag(unprotected_tag)


def get_group_id(tag: ProtectedTag) -> TagGroupId | None:
    return cast(str | None, tag.get(GROUP_ID_ATTR, None))


def _make_id(
    id_counters: IdCounters,
    name: Literal["tag_id", "group_id"],
) -> str:
    setattr(id_counters, name, getattr(id_counters, name) + 1)
    return f"{getattr(id_counters, name)}"
