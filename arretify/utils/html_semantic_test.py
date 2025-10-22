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
from enum import Enum
from typing import Annotated
import unittest

from bs4 import BeautifulSoup

from .html_semantic import (
    SemanticTagData,
    SemanticTagSpec,
    create_semantic_tag_spec_no_data,
    is_semantic_tag,
    Bool,
    StrList,
    enum_serializer,
    update_data,
    make_semantic_tag,
    set_semantic_tag_data,
    get_semantic_tag_data,
    enum_list_serializer,
    css_selector,
)


class SemanticTagDataTestCase(unittest.TestCase):

    def setUp(self) -> None:
        self.spec_no_data = create_semantic_tag_spec_no_data(
            spec_name="test_no_data",
            tag_name="div",
        )

        class CustomData(SemanticTagData):
            value: str

        self.spec_with_data = SemanticTagSpec(
            spec_name="test_with_data",
            tag_name="div",
            data_model=CustomData,
        )

        self.soup = BeautifulSoup("", "html.parser")

        self.tag_with_data = self.soup.new_tag("div")
        self.tag_with_data["data-spec"] = self.spec_with_data.spec_name


class TestCssSelector(unittest.TestCase):

    def test_returns_attribute_selector(self):
        # ARRANGE
        spec_test = create_semantic_tag_spec_no_data(
            spec_name="test_spec",
            tag_name="div",
        )

        # ACT
        selector = css_selector(spec_test)

        # ASSERT
        assert selector == '[data-spec="test_spec"]'


class TestMakeSemanticTag(SemanticTagDataTestCase):

    def test_creates_tag_with_spec_name(self):
        # ACT
        tag = make_semantic_tag(self.soup, self.spec_no_data)

        # ASSERT
        assert tag.name == "div"
        assert tag["data-spec"] == "test_no_data"

    def test_creates_tag_with_custom_data(self):
        # ARRANGE
        data = self.spec_with_data.data_model(value="hello")

        # ACT
        tag = make_semantic_tag(self.soup, self.spec_with_data, data=data)

        # ASSERT
        assert tag["data-value"] == "hello"


class TestIsSemanticTag(unittest.TestCase):

    def setUp(self):
        self.soup = BeautifulSoup("", "html.parser")

        self.model_bla = SemanticTagSpec(
            spec_name="bla",
            tag_name="div",
            data_model=SemanticTagData,
        )

        self.model_bli = SemanticTagSpec(
            spec_name="bli",
            tag_name="div",
            data_model=SemanticTagData,
        )

    def test_any_semantic_tag(self):
        # Arrange
        tag = self.soup.new_tag("div")
        tag["data-spec"] = "arretify-test"

        # Act
        result = is_semantic_tag(tag)

        # Assert
        assert result is True

    def test_is_not_tag(self):
        # Arrange
        not_a_tag = "just a string"

        # Act
        result = is_semantic_tag(not_a_tag)

        # Assert
        assert result is False

    def test_spec_in(self):
        # Arrange
        tag = self.soup.new_tag("div")
        tag["data-spec"] = "bla"

        # Act
        result1 = is_semantic_tag(tag, spec_in=[self.model_bla])
        result2 = is_semantic_tag(tag, spec_in=[self.model_bli])

        # Assert
        assert result1 is True
        assert result2 is False

    def test_tag_name_in(self):
        # Arrange
        tag = self.soup.new_tag("div")
        tag["data-spec"] = "bla"

        # Act
        result1 = is_semantic_tag(tag, tag_name_in=["div"])
        result2 = is_semantic_tag(tag, tag_name_in=["span"])

        # Assert
        assert result1 is True
        assert result2 is False


class TestSemanticTagData(unittest.TestCase):

    def setUp(self) -> None:
        class Color(Enum):
            RED = "red"
            GREEN = "green"

        class Model(SemanticTagData):
            flag: Bool
            items: StrList
            color: Annotated[Color, enum_serializer]
            color_choices: Annotated[list[Color], enum_list_serializer]

        self.Model = Model
        self.Color = Color

    def test_forbidden_field_names(self) -> None:
        # ACT & ASSERT
        with self.assertRaises(ValueError) as cm:

            class BadModel1(SemanticTagData):
                tag_id: str

        assert "tag_id" in str(cm.exception)

    def test_none_is_removed(self) -> None:
        # Arrange
        class Model(SemanticTagData):
            bla: Bool | None = None

        # Act
        m = Model()

        # Assert
        assert m.model_dump() == {}

    def test_build_with_native_values(self) -> None:
        # Act
        m = self.Model(
            flag=True,
            items=["a", "b"],
            color=self.Color.RED,
            color_choices=[self.Color.RED, self.Color.GREEN],
        )

        # Assert
        assert m.flag is True
        assert m.items == ["a", "b"]
        assert m.color == self.Color.RED
        assert m.model_dump() == {
            "flag": "true",
            "items": "a,b",
            "color": "red",
            "color_choices": "red,green",
        }

    def test_build_with_string_values(self) -> None:
        # Act
        m = self.Model(flag="false", items="a, b", color="green", color_choices=["green", "red"])

        # Assert
        assert m.flag is False
        assert m.items == ["a", "b"]
        assert m.color == self.Color.GREEN
        assert m.model_dump() == {"items": "a,b", "color": "green", "color_choices": "green,red"}

    def test_error_if_string_item_with_comma(self) -> None:
        # Arrange
        m = self.Model(flag=True, items=["a,"], color="red", color_choices=["red", "green"])

        # Act & Assert
        with self.assertRaises(ValueError):
            m.model_dump()


class TestGetSemanticTagData(SemanticTagDataTestCase):

    def test_get_data_attributes(self):
        # ARRANGE
        self.tag_with_data["data-value"] = "hello"

        # ACT
        data = get_semantic_tag_data(self.spec_with_data, self.tag_with_data)

        # ASSERT
        assert data.value == "hello"

    def test_with_reserved_data_attribute(self):
        # ARRANGE
        self.tag_with_data["data-group_id"] = "bla"
        self.tag_with_data["data-value"] = "coucou"

        # ACT
        data = get_semantic_tag_data(self.spec_with_data, self.tag_with_data)

        # ASSERT
        assert data.value == "coucou"


class TestSetSemanticTagData(SemanticTagDataTestCase):

    def test_set_data_attributes(self):
        # ARRANGE
        data = self.spec_with_data.data_model(value="hello")

        # ACT
        set_semantic_tag_data(self.spec_with_data, self.tag_with_data, data)

        # ASSERT
        assert self.tag_with_data["data-value"] == "hello"


class TestUpdateData(unittest.TestCase):

    def test_update_single_field(self) -> None:
        # ARRANGE
        class Model(SemanticTagData):
            name: str
            age: int

        original = Model(name="Alice", age=30)

        # ACT
        updated = update_data(original, age=31)

        # ASSERT
        assert updated.name == "Alice"
        assert updated.age == 31
        assert updated is not original  # New instance

    def test_validation_runs_on_update(self) -> None:
        # ARRANGE
        class Model(SemanticTagData):
            age: int

        original = Model(age=30)

        # ACT & ASSERT
        with self.assertRaises(Exception):  # Validation error
            update_data(original, age="not-a-number")
