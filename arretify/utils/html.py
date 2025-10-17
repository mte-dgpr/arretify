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
from typing import Literal, Sequence, TypeGuard, Iterable, Iterator

from bs4 import Tag

from arretify.types import (
    IdCounters,
    PageElementOrString,
    TagGroupId,
    TagId,
)
from arretify.utils.functional import iter_func_to_list


INLINE_TAG_TYPES = ["br"]

TAG_ID_ATTR = "data-element_id"
# TODO:RENAME : rename to data-tag_id
GROUP_ID_ATTR = "data-group_id"


def is_tag(
    tag: PageElementOrString,
    tag_name_in: Sequence[str] | None = None,
) -> TypeGuard[Tag]:
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
    elements: Iterable[PageElementOrString],
) -> Iterator[PageElementOrString]:
    for element in elements:
        if not is_tag(element, tag_name_in=INLINE_TAG_TYPES):
            yield element


def ensure_tag_id(id_counters: IdCounters, tag: Tag) -> TagId:
    current_tag_id = tag.get(TAG_ID_ATTR, None)
    if current_tag_id is None:
        tag[TAG_ID_ATTR] = _make_id(id_counters, "element_id")
    return tag[TAG_ID_ATTR]


def make_group_id(id_counters: IdCounters) -> TagGroupId:
    return _make_id(id_counters, "group_id")


def set_group_id(tag: Tag, group_id: TagGroupId) -> TagGroupId:
    current_group_id = tag.get(GROUP_ID_ATTR, None)
    if current_group_id is not None and current_group_id != group_id:
        raise ValueError(f"Tag already has a different group_id: {current_group_id}")
    tag[GROUP_ID_ATTR] = group_id
    return group_id


def get_group_id(tag: Tag) -> TagGroupId | None:
    return tag.get(GROUP_ID_ATTR, None)


def _make_id(
    id_counters: IdCounters,
    name: Literal["element_id", "group_id"],
) -> str:
    setattr(id_counters, name, getattr(id_counters, name) + 1)
    return f"{getattr(id_counters, name)}"
