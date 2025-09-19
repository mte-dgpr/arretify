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
import json
from typing import Dict, Iterable, Sequence
from bs4 import BeautifulSoup, Tag

from arretify.types import DataElementDataDict, PageElementOrString, DataElementSchema
from arretify.utils.split_merge import (
    split_elements,
    map_splitted_elements,
)
from arretify.utils.html_split_merge import group_strings_splitter
from arretify.utils.strings import (
    merge_strings,
)
from .html import SHARED_DATA_KEYS


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
    element["class"] = schema.css_class
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


SegmentationTagDataDict = Dict[str, str | int | float | bool | None | list[str] | list[int]]


def make_segmentation_tag(
    soup: BeautifulSoup,
    tag_name: str,
    contents: Iterable[PageElementOrString] | None = None,
    data: SegmentationTagDataDict | None = None,
) -> Tag:
    if contents is None:
        contents = []
    if data is None:
        data = {}
    element = make_new_tag(soup, tag_name, contents=contents)
    update_segmentation_tag_data(element, data)
    return element


def update_segmentation_tag_data(element: Tag, data: SegmentationTagDataDict):
    for key, value in data.items():
        element[f"data-{key}"] = json.dumps(value, ensure_ascii=False)


def read_segmentation_tag_data(element: Tag) -> SegmentationTagDataDict:
    data: SegmentationTagDataDict = {}
    for key, value in element.attrs.items():
        if key.startswith("data-"):
            data_key = key[5:]
            data_value = json.loads(value)
            data[data_key] = data_value
    return data


def wrap_in_tag(
    soup: BeautifulSoup,
    elements: Sequence[PageElementOrString],
    tag_name: str,
) -> list[Tag]:
    wrapped: list[Tag] = []
    for element in elements:
        if isinstance(element, str) and element.strip():
            container = soup.new_tag(tag_name)
            wrapped.append(container)
            container.append(element)
    return wrapped


def make_new_tag(
    soup: BeautifulSoup,
    tag_name: str,
    contents: Iterable[PageElementOrString] | None = None,
) -> Tag:
    # We must be careful not to move elements from one part of the tree to another
    # because that might have unexpected side-effects.
    # For example, if iterating over the children of a tag and moving one of them
    # to a new tag, the list currenlty being iterated is modified.
    # This is why we work with copies here.
    cloned_contents: list[PageElementOrString]
    if contents is None:
        cloned_contents = []
    else:
        cloned_contents = [copy(element) for element in contents]

    element = soup.new_tag(tag_name)
    element.extend(
        map_splitted_elements(
            split_elements(
                cloned_contents,
                group_strings_splitter,
            ),
            merge_strings,
        )
    )
    return element


def replace_children(
    tag: Tag,
    new_children: Iterable[PageElementOrString],
) -> Tag:
    tag.clear()
    tag.extend(new_children)
    return tag
