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
from typing import List, Iterable, cast, TypeGuard

from bs4 import BeautifulSoup, Tag

from arretify.utils.merge import merge_strings_ignore_page_elements
from arretify.types import (
    DataElementSchema,
    DataElementDataDict,
    PageElementOrString,
    ElementId,
    ElementGroupId,
)


SHARED_DATA_KEYS = [
    "error_codes",
]
_ELEMENT_ID_COUNTER = 0
_GROUP_ID_COUNTER = 0


def make_css_class(schema: DataElementSchema):
    return f"dsr-{schema.name}"


def assign_element_id(tag: Tag) -> ElementId:
    global _ELEMENT_ID_COUNTER
    if "data-element_id" in tag.attrs:
        return cast(ElementId, tag["data-element_id"])
    _ELEMENT_ID_COUNTER += 1
    element_id: ElementId = f"{_ELEMENT_ID_COUNTER}"
    tag["data-element_id"] = element_id
    return element_id


def assign_group_id(tag: Tag, group_id: ElementGroupId) -> None:
    tag["data-group_id"] = group_id


def make_group_id() -> ElementGroupId:
    global _GROUP_ID_COUNTER
    _GROUP_ID_COUNTER += 1
    return f"{_GROUP_ID_COUNTER}"


def get_group_id(tag: Tag) -> ElementGroupId | None:
    group_id = tag.get("data-group_id")
    if group_id is not None:
        return cast(ElementGroupId, group_id)
    return None


def make_data_tag(
    soup: BeautifulSoup,
    schema: DataElementSchema,
    contents: Iterable[PageElementOrString] | None = None,
    data: DataElementDataDict | None = None,
) -> Tag:
    if contents is None:
        contents = []
    if data is None:
        data = {}
    element = make_new_tag(soup, schema.tag_name, contents=contents)
    element["class"] = [make_css_class(schema)]
    for key in schema.data_keys:
        try:
            data_value = data[key]
        except KeyError:
            raise KeyError(f'Missing key "{key}" for schema "{schema.name}"')
        if data_value is not None:
            element[f"data-{key}"] = data_value

    for key in SHARED_DATA_KEYS:
        if key in data:
            data_value = data[key]
            if data_value is not None:
                element[f"data-{key}"] = data_value

    return element


def wrap_in_tag(
    soup: BeautifulSoup,
    elements: List[PageElementOrString],
    tag_name: str,
) -> List[Tag]:
    wrapped: List[Tag] = []
    for element in elements:
        if isinstance(element, str) and element.strip():
            container = soup.new_tag(tag_name)
            wrapped.append(container)
            container.append(element)
    return wrapped


def make_ul(soup: BeautifulSoup, elements: List[PageElementOrString]):
    ul = soup.new_tag("ul")
    for element in elements:
        if isinstance(element, Tag) and element.name == "li":
            li = element
        else:
            li = make_li(soup, [element])
        ul.append(li)
    return ul


def make_li(soup: BeautifulSoup, elements: List[PageElementOrString]):
    li = soup.new_tag("li")
    li.extend(elements)
    return li


def make_new_tag(
    soup: BeautifulSoup,
    tag_name: str,
    contents: Iterable[PageElementOrString] | None = None,
) -> Tag:
    if contents is None:
        contents = []
    element = soup.new_tag(tag_name)
    element.extend(merge_strings_ignore_page_elements(contents))
    return element


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


def replace_children(
    tag: Tag,
    new_children: Iterable[PageElementOrString],
) -> None:
    tag.clear()
    tag.extend(new_children)


def is_tag_and_matches(
    tag: PageElementOrString, css_classes_in: List[str] | None = None
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
                return True
        return False

    return True
