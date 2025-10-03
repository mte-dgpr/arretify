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
from typing import Iterable, Sequence, TypeGuard
from bs4 import BeautifulSoup, Tag
from arretify.types import DataElementDataDict, PageElementOrString, SemanticTagSchema
from arretify.utils.html import is_tag
from arretify.utils.html_create import make_new_tag


SCHEMA_NAME_DATA_ATTR = "data-schema"
SHARED_DATA_KEYS = [
    "error_codes",
]


def is_semantic_tag(
    tag: PageElementOrString,
    schema_in: Sequence[SemanticTagSchema] | None = None,
    tag_name_in: Sequence[str] | None = None,
) -> TypeGuard[Tag]:
    """
    Check if a tag is a semantic tag, i.e. has a CSS class starting with "arretify-".
    """
    if not is_tag(tag, tag_name_in=tag_name_in):
        return False

    actual_schema_name = tag.get(SCHEMA_NAME_DATA_ATTR, None)
    if actual_schema_name is None:
        return False

    if schema_in is not None:
        schema_name_in = {schema.name for schema in schema_in}
        if actual_schema_name not in schema_name_in:
            return False
    return True


def css_selector(schema: SemanticTagSchema) -> str:
    return f'[{SCHEMA_NAME_DATA_ATTR}="{schema.name}"]'


def make_semantic_tag(
    soup: BeautifulSoup,
    schema: SemanticTagSchema,
    contents: Iterable[PageElementOrString] | None = None,
    data: DataElementDataDict | None = None,
) -> Tag:
    if contents is None:
        contents = []
    if data is None:
        data = {}
    element = make_new_tag(soup, schema.tag_name, contents=contents)
    element[SCHEMA_NAME_DATA_ATTR] = schema.name
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
