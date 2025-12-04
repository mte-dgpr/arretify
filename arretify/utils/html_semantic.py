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
from typing import Annotated, Callable, Generic, Sequence, Type, TypeGuard, TypeVar, cast

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    SerializerFunctionWrapHandler,
    model_serializer,
)
from pydantic.functional_serializers import PlainSerializer

from arretify.errors import ErrorCodes
from arretify.types import ProtectedSoup, ProtectedTag, ProtectedTagOrStr
from arretify.utils.html import GROUP_ID_ATTR, TAG_ID_ATTR, is_tag, set_attribute

_SPEC_DATA_ATTR = "data-spec"
_RESERVED_DATA_ATTRIBUTES = [_SPEC_DATA_ATTR, TAG_ID_ATTR, GROUP_ID_ATTR]
_RESERVED_DATA_FIELD_NAMES = [key[len("data-") :] for key in _RESERVED_DATA_ATTRIBUTES]


# -------------------- Pydantic fields -------------------- #
def _serialize_bool(v: bool) -> str | None:
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


def _parse_int_list(v: list[int] | str) -> list[int]:
    if isinstance(v, list):
        return v
    if isinstance(v, str):
        str_items = _parse_str_list(v)
        return [int(item) for item in str_items]
    raise ValueError(f'Invalid integer list value: "{v}"')


def _serialize_int_list(v: list[int]) -> str:
    if isinstance(v, list):
        return _serialize_str_list([str(item) for item in v])
    raise ValueError(f'Invalid integer list value: "{v}"')


def _serialize_enum_list(v: list[Enum]) -> str:
    return _serialize_str_list([e.value for e in v])


def _serialize_enum(v: Enum) -> str:
    return v.value


enum_serializer = PlainSerializer(_serialize_enum, return_type=str)
enum_list_parser = BeforeValidator(_parse_str_list)
enum_list_serializer = PlainSerializer(_serialize_enum_list, return_type=str)


Bool = Annotated[bool, PlainSerializer(_serialize_bool, return_type=str)]


StrList = Annotated[
    list[str],
    BeforeValidator(_parse_str_list),
    PlainSerializer(_serialize_str_list, return_type=str),
]


IntList = Annotated[
    list[int],
    BeforeValidator(_parse_int_list),
    PlainSerializer(_serialize_int_list, return_type=str),
]


# -------------------- Base models -------------------- #
TSemanticTagData = TypeVar("TSemanticTagData", bound="SemanticTagData")


class Contents:
    """
    Namespace for specifying allowed contents of semantic tags.
    """

    @dataclass(frozen=True, eq=True)
    class Str:
        pass

    @dataclass(frozen=True, eq=True)
    class Tag:
        tag_name: str

    @dataclass(frozen=True, eq=True)
    class SemanticTag:
        spec_name: str

    Tuple = tuple[Str | Tag | SemanticTag, ...]


_REGISTRY: dict[str, "SemanticTagSpec"] = {}


class SemanticTagData(BaseModel):
    error_codes: Annotated[list[ErrorCodes], enum_list_parser, enum_list_serializer] | None = None

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


# Set both frozen and eq to True to make dataclass hashable.
# This is required to use SemanticTagSpec as dict keys if needed.
@dataclass(frozen=True, eq=True)
class SemanticTagSpec(Generic[TSemanticTagData]):
    """
    Defines the structure and behavior of a semantic HTML tag type.
    """

    spec_name: str
    """
    Unique identifier for the semantic tag type.
    """

    tag_name: str | Callable[[ProtectedSoup, TSemanticTagData], ProtectedTag]
    """
    HTML tag name to use (e.g., 'div', 'span', 'section'), or a callable that creates
    a ProtectedTag given the semantic tag data (useful for example for headings).
    """

    data_model: Type[TSemanticTagData]
    """Pydantic model class for validating tag data attributes"""

    allowed_contents: Contents.Tuple | None = tuple()
    """
    Allowed contents inside this semantic tag.
    Use Contents.Str, Contents.Tag, Contents.SemanticTag to specify allowed types.
    If value is `None`, any content is allowed. This should not be used except for very specific
    cases.
    """

    is_allowed_anywhere: bool = False
    """
    Whether this semantic tag can appear anywhere in the document.
    If True, this tag is not subject to content restrictions.
    """

    def __post_init__(self):
        _REGISTRY[self.spec_name] = self


def create_semantic_tag_spec_no_data(
    spec_name: str,
    tag_name: str,
    allowed_contents: Contents.Tuple | None = tuple(),
    is_allowed_anywhere: bool = False,
) -> SemanticTagSpec[SemanticTagData]:
    """
    Create a SemanticTagSpec with the default SemanticTagData model.
    """
    return SemanticTagSpec(
        spec_name=spec_name,
        tag_name=tag_name,
        data_model=SemanticTagData,
        allowed_contents=allowed_contents,
        is_allowed_anywhere=is_allowed_anywhere,
    )


# -------------------- Semantic html utils -------------------- #
def is_semantic_tag(
    tag: ProtectedTagOrStr,
    spec_in: Sequence[SemanticTagSpec] | None = None,
    tag_name_in: Sequence[str] | None = None,
) -> TypeGuard[ProtectedTag]:
    """
    Check if a tag is a semantic tag.

    Optionally this function checks also that :
    - tag name is included in the given `tag_name_in` list.
    - semantic tag is included in the given `spec_in` list.
    """
    if not is_tag(tag, tag_name_in=tag_name_in):
        return False

    actual_spec_name = tag.get(_SPEC_DATA_ATTR, None)
    if actual_spec_name is None:
        return False

    if spec_in is not None:
        spec_name_in = {tag_spec.spec_name for tag_spec in spec_in}
        if actual_spec_name not in spec_name_in:
            return False
    return True


def css_selector(spec: SemanticTagSpec[TSemanticTagData]) -> str:
    return f'[{_SPEC_DATA_ATTR}="{spec.spec_name}"]'


def get_semantic_tag_spec(tag: ProtectedTag) -> SemanticTagSpec:
    actual_spec_name = tag.get(_SPEC_DATA_ATTR, None)
    if actual_spec_name is None:
        raise ValueError("Tag is not a semantic tag (missing spec attribute)")

    spec = _REGISTRY.get(cast(str, actual_spec_name), None)
    if spec is None:
        raise ValueError(f"Unknown semantic tag spec: {actual_spec_name}")

    return spec


def get_semantic_tag_data(
    spec: SemanticTagSpec[TSemanticTagData], tag: ProtectedTag
) -> TSemanticTagData:
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
    spec: SemanticTagSpec[TSemanticTagData], tag: ProtectedTag, data: TSemanticTagData
) -> None:
    _ensure_matching_spec(spec, tag)
    for key, value in data.model_dump().items():
        set_attribute(tag, f"data-{key}", str(value))


def update_semantic_tag_data(
    spec: SemanticTagSpec[TSemanticTagData],
    tag: ProtectedTag,
    **kwargs,
) -> TSemanticTagData:
    """
    Update properties of the semantic tag data, by replacing
    the existing data with a new instance with updated fields.
    """
    current_data = get_semantic_tag_data(spec, tag)
    new_data = update_data(current_data, **kwargs)
    set_semantic_tag_data(spec, tag, new_data)
    return new_data


def _ensure_matching_spec(
    spec: SemanticTagSpec,
    tag: ProtectedTag,
) -> None:
    if not is_semantic_tag(tag, spec_in=[spec]):
        raise ValueError(f"Expected semantic tag {spec.spec_name}")


def update_data(obj: TSemanticTagData, **kwargs) -> TSemanticTagData:
    """
    Replace properties of a SemanticTagData object, returning
    a new instance and running validation.
    """
    return type(obj).model_validate(obj.model_dump() | kwargs)
