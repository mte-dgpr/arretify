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
from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Sequence, TypeGuard, Annotated, TypeVar, Type, Generic

from pydantic import (
    BaseModel,
    BeforeValidator,
    SerializerFunctionWrapHandler,
    ConfigDict,
    model_serializer,
)
from pydantic.functional_serializers import PlainSerializer
from bs4 import BeautifulSoup, Tag

from arretify.errors import ErrorCodes
from arretify.types import PageElementOrString
from arretify.utils.html import GROUP_ID_ATTR, TAG_ID_ATTR, is_tag
from arretify.utils.html_create import make_new_tag


_SPEC_DATA_ATTR = "data-schema"
# TODO:RENAME : rename to data-spec

_RESERVED_DATA_ATTRIBUTES = [_SPEC_DATA_ATTR, TAG_ID_ATTR, GROUP_ID_ATTR]
_RESERVED_DATA_FIELD_NAMES = [key[len("data-") :] for key in _RESERVED_DATA_ATTRIBUTES]


# -------------------- Pydantic fields -------------------- #
def _serialize_bool(v: bool) -> str:
    return "true" if v else None


def _parse_str_list(v: list[str] | str) -> list[str]:
    if isinstance(v, list):
        return v
    if isinstance(v, str):
        return [item.strip() for item in v.split(",") if item.strip()]
    raise ValueError(f'Invalid string list value: "{v}"')


def _serialize_str_list(v: list[str]) -> str:
    if isinstance(v, list):
        for item in v:
            if "," in item:
                raise ValueError(f'String list items cannot contain commas: "{item}"')
        return ",".join(v)
    raise ValueError(f'Invalid string list value: "{v}"')


def _serialize_enum_list(v: list[Enum]) -> str:
    return _serialize_str_list([e.value for e in v])


def _serialize_enum(v: Enum) -> str:
    return v.value


enum_serializer = PlainSerializer(_serialize_enum, return_type=str)
enum_list_serializer = PlainSerializer(_serialize_enum_list, return_type=str)


Bool = Annotated[bool, PlainSerializer(_serialize_bool, return_type=str)]


StrList = Annotated[
    list[str],
    BeforeValidator(_parse_str_list),
    PlainSerializer(_serialize_str_list, return_type=str),
]


# -------------------- Base models -------------------- #
_REGISTRY: dict[str, "SemanticTagSpec"] = {}


class SemanticTagData(BaseModel):
    error_codes: Annotated[list[ErrorCodes], enum_list_serializer] | None = None

    model_config = ConfigDict(extra="forbid", frozen=True)

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs):
        super().__pydantic_init_subclass__(**kwargs)
        # Check if any forbidden field names are defined in the subclass
        for field_name in cls.model_fields:
            if field_name in _RESERVED_DATA_FIELD_NAMES:
                raise ValueError(
                    f"Field name '{field_name}' is reserved and cannot be used in {cls.__name__}."
                )

    @model_serializer(mode="wrap")
    def serialize_model(self, handler: SerializerFunctionWrapHandler) -> dict[str, object]:
        # Custom serialization to remove None values
        serialized = handler(self)
        for key in list(serialized):
            if serialized[key] is None:
                del serialized[key]
        return serialized


TSemanticTagData = TypeVar("TSemanticTagData", bound=SemanticTagData)


@dataclass(frozen=True)
class SemanticTagSpec(Generic[TSemanticTagData]):
    """
    Defines the structure and behavior of a semantic HTML tag type.

    Attributes:
        spec_name: Unique identifier for the semantic tag type
        tag_name: HTML tag name to use (e.g., 'div', 'span', 'section')
        data_model: Pydantic model class for validating tag data attributes
    """

    spec_name: str
    tag_name: str
    data_model: Type[TSemanticTagData] = SemanticTagData

    def __post_init__(self):
        _REGISTRY[self.spec_name] = self


# -------------------- Semantic html utils -------------------- #
def is_semantic_tag(
    tag: PageElementOrString,
    spec_in: Sequence[SemanticTagSpec] | None = None,
    tag_name_in: Sequence[str] | None = None,
) -> TypeGuard[Tag]:
    """
    Check if a tag is a semantic tag.

    Optionally this function checks also that :
    - tag name is included in the given `tag_name_in` list.
    - semantic tag is included in the given `spec_in` list.
    """
    if not is_tag(tag, tag_name_in=tag_name_in):
        return False

    actual_semantic_name = tag.get(_SPEC_DATA_ATTR, None)
    if actual_semantic_name is None:
        return False

    if spec_in is not None:
        semantic_name_in = {tag_spec.spec_name for tag_spec in spec_in}
        if actual_semantic_name not in semantic_name_in:
            return False
    return True


def css_selector(spec: SemanticTagSpec[TSemanticTagData]) -> str:
    return f'[{_SPEC_DATA_ATTR}="{spec.spec_name}"]'


def make_semantic_tag(
    soup: BeautifulSoup,
    spec: SemanticTagSpec[TSemanticTagData],
    contents: Iterable[PageElementOrString] | None = None,
    data: TSemanticTagData | None = None,
) -> Tag:
    if contents is None:
        contents = []

    # Create data instance if not provided
    if data is None:
        data = spec.data_model()

    # Create the HTML tag
    tag = make_new_tag(soup, spec.tag_name, contents=contents)
    tag[_SPEC_DATA_ATTR] = spec.spec_name

    # Set data attributes from the validated data instance
    set_semantic_tag_data(spec, tag, data)

    return tag


def get_semantic_tag_data(spec: SemanticTagSpec[TSemanticTagData], tag: Tag) -> TSemanticTagData:
    _ensure_matching_spec(spec, tag)
    raw_data: dict[str, str] = {}
    for key, value in tag.attrs.items():
        if key in _RESERVED_DATA_ATTRIBUTES:
            continue
        if key.startswith("data-"):
            data_key = key[len("data-") :]
            raw_data[data_key] = value
    return spec.data_model.model_validate(raw_data)


def set_semantic_tag_data(
    spec: SemanticTagSpec[TSemanticTagData], tag: Tag, data: TSemanticTagData
) -> None:
    _ensure_matching_spec(spec, tag)
    for key, value in data.model_dump().items():
        tag[f"data-{key}"] = str(value)


def _ensure_matching_spec(
    spec: SemanticTagSpec,
    tag: Tag,
) -> None:
    if not is_semantic_tag(tag, spec_in=[spec]):
        raise ValueError(f"Expected semantic tag {spec.spec_name}")


def update_data(obj: TSemanticTagData, **kwargs) -> TSemanticTagData:
    """
    Replace properties of a SemanticTagData object, returning
    a new instance and running validation.
    """
    return type(obj).model_validate(obj.model_dump() | kwargs)
