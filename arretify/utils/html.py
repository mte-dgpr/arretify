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
from typing import List, cast, TypeGuard, Literal, Iterable, Iterator

from bs4 import Tag

from arretify.types import (
    DataElementDataDict,
    PageElementOrString,
    ElementId,
    ElementGroupId,
    IdCounters,
)
from arretify.utils.functional import iter_func_to_list


INLINE_TAG_TYPES = ["br"]


SHARED_DATA_KEYS = [
    "error_codes",
]

_Id = str
_IdName = Literal["element_id", "group_id"]


def ensure_element_id(id_counters: IdCounters, tag: Tag) -> ElementId:
    current_id = _get_id_from_tag(tag, "element_id")
    if current_id is not None:
        return cast(ElementId, current_id)
    return _set_id_to_tag(tag, "element_id", _make_id(id_counters, "element_id"))


def set_group_id(tag: Tag, group_id: ElementGroupId) -> ElementGroupId:
    return _set_id_to_tag(tag, "group_id", group_id)


def make_group_id(id_counters: IdCounters) -> ElementGroupId:
    return _make_id(id_counters, "group_id")


def get_group_id(tag: Tag) -> ElementGroupId | None:
    return _get_id_from_tag(tag, "group_id")


def _make_id(
    id_counters: IdCounters,
    name: _IdName,
) -> _Id:
    setattr(id_counters, name, getattr(id_counters, name) + 1)
    return f"{getattr(id_counters, name)}"


def _set_id_to_tag(
    tag: Tag,
    name: _IdName,
    id_value: _Id,
) -> _Id:
    tag[f"data-{name}"] = id_value
    return id_value


def _get_id_from_tag(tag: Tag, name: _IdName) -> _Id | None:
    id_value = tag.get(f"data-{name}")
    if id_value is not None:
        return cast(_Id, id_value)
    return None


def parse_bool_attribute(value: str) -> bool:
    return value == "true"


def render_bool_attribute(value: bool) -> str:
    return "true" if value else "false"


def parse_str_list_attribute(value: str) -> List[str]:
    return value.split(",")


def render_str_list_attribute(value: List[str]) -> str:
    for item in value:
        if "," in item:
            raise ValueError(f'Invalid item "{item}" in list')
    return ",".join(value)


def set_data_attributes(tag: Tag, data: DataElementDataDict) -> None:
    for key, value in data.items():
        if value is not None:
            tag[f"data-{key}"] = value


def is_tag_and_matches(
    tag: PageElementOrString,
    css_classes_in: List[str] | None = None,
    tag_name_in: List[str] | None = None,
) -> TypeGuard[Tag]:
    """
    Check if a tag has any of the specified CSS classes.
    """
    if not isinstance(tag, Tag):
        return False

    if css_classes_in is not None:
        actual_css_classes = tag.get_attribute_list("class", [])
        for css_class in actual_css_classes:
            # If you set the 'class' on a tag as a string, it seems like you will
            # get a string back, e.g. :
            #   tag.class = "my-class my-other-class"
            #   tag.get_attribute_list("class") -> ["my-class my-other-class"]
            if " " in css_class:
                raise RuntimeError(
                    "CSS class contains spaces. Please use a list of classes instead."
                )
        for css_class in css_classes_in:
            if css_class in actual_css_classes:
                break
        else:
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
        if not is_tag_and_matches(element, tag_name_in=INLINE_TAG_TYPES):
            yield element
