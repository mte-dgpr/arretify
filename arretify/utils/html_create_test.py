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
import unittest

from bs4 import BeautifulSoup

from arretify.types import ProtectedTagOrStr, protect_soup, unprotect_tag
from arretify.utils.html_semantic import (
    Contents,
    SemanticTagData,
    SemanticTagSpec,
    create_semantic_tag_spec_no_data,
)
from arretify.utils.html_semantic_test import SemanticTagDataTestCase

from .html_create import (
    InvalidContentsError,
    _unprotect_page_elements,
    _validate_semantic_tag_contents,
    _validate_tag_contents,
    make_new_tag,
    make_semantic_tag,
    replace_children,
    upgrade_to_semantic_tag,
)


class TestMakeNewTag(unittest.TestCase):

    def setUp(self):
        self.soup = BeautifulSoup("", features="html.parser")

    def test_make_new_tag_from_dynamically_mutated_list_of_children(self):
        """
        When passing an element as `contents` to `make_new_tag`, that element
        is moved to another parent during the call, and that shouldn't affect
        iteration over the original list.
        """
        # Arrange
        soup = BeautifulSoup("<span>bla</span><span>blo</span>", features="html.parser")

        # Act
        elements = []
        for child in soup.contents:
            elements.append(make_new_tag(self.soup, "div", contents=[child]))

        # Assert
        assert len(elements) == 2
        assert str(elements[0]) == "<div><span>bla</span></div>"
        assert str(elements[1]) == "<div><span>blo</span></div>"

    def test_with_contents_iterator(self):
        # ARRANGE
        contents = (f"Item {i}" for i in range(3))

        # ACT
        tag = make_new_tag(self.soup, "ul", contents=contents)

        # ASSERT
        assert str(tag) == "<ul>Item 0Item 1Item 2</ul>"

    def test_validation_is_performed_on_contents(self):
        # ARRANGE
        spec = create_semantic_tag_spec_no_data(
            spec_name="some_spec",
            tag_name="div",
        )
        contents = [
            "blabla ",
            # Semantic tag not allowed in plain tag contents
            make_semantic_tag(self.soup, spec),
        ]

        # ACT & ASSERT
        with self.assertRaises(InvalidContentsError):
            make_new_tag(self.soup, "p", contents=contents)

    def test_attrs_parameter(self):
        # ACT
        tag = make_new_tag(
            self.soup,
            "div",
            contents=["text"],
            attrs={"class": "my-class", "alt": "some-text"},
        )

        # ASSERT
        assert tag.name == "div"
        assert tag["class"] == "my-class"
        assert tag["alt"] == "some-text"

    def test_attrs_parameter_with_data_attribute_raises(self):
        # ACT & ASSERT
        with self.assertRaises(ValueError):
            make_new_tag(
                self.soup,
                "div",
                contents=["text"],
                attrs={"data-spec": "some-spec"},
            )


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

    def test_validation_is_performed_on_contents(self):
        # ARRANGE
        spec = create_semantic_tag_spec_no_data(
            spec_name="some_spec",
            tag_name="div",
            allowed_contents=(Contents.Str(),),
        )
        contents = [
            "blabla ",
            # <span> not allowed in spec
            make_new_tag(self.soup, "span", contents=["text"]),
        ]

        # ACT & ASSERT
        with self.assertRaises(InvalidContentsError):
            make_semantic_tag(self.soup, spec, contents=contents)

    def test_with_contents_iterator(self):
        # ARRANGE
        contents = (f"Item {i}" for i in range(3))

        # ACT
        tag = make_semantic_tag(self.soup, self.spec_no_data, contents=contents)

        # ASSERT
        assert str(tag) == '<div data-spec="test_no_data">Item 0Item 1Item 2</div>'

    def test_attrs_parameter(self):
        # ACT
        tag = make_semantic_tag(
            self.soup,
            self.spec_no_data,
            contents=["text"],
            attrs={"class": "my-class", "alt": "some-text"},
        )

        # ASSERT
        assert tag.name == "div"
        assert tag["data-spec"] == "test_no_data"
        assert tag["class"] == "my-class"
        assert tag["alt"] == "some-text"


class TestUpgradeToSemanticTag(unittest.TestCase):

    def setUp(self):
        self.soup = protect_soup(BeautifulSoup("", "html.parser"))

        self.some_spec = SemanticTagSpec(
            spec_name="some_spec",
            tag_name="span",
            data_model=SemanticTagData,
            allowed_contents=(Contents.Str(),),
        )

    def test_upgrades_plain_tag_to_semantic_tag(self):
        # ARRANGE
        plain_tag = make_new_tag(self.soup, "span", contents=["text"])

        # ACT
        semantic_tag = upgrade_to_semantic_tag(plain_tag, self.some_spec)

        # ASSERT
        assert semantic_tag.name == "span"
        assert semantic_tag["data-spec"] == "some_spec"
        assert str(semantic_tag) == '<span data-spec="some_spec">text</span>'


class TestValidateSemanticTagContents(unittest.TestCase):

    def setUp(self) -> None:
        self.soup = protect_soup(BeautifulSoup("", "html.parser"))

        self.some_spec = SemanticTagSpec(
            spec_name="some_spec",
            tag_name="span",
            data_model=SemanticTagData,
        )

    def test_only_str_allowed(self) -> None:
        # ARRANGE
        spec_only_str = SemanticTagSpec(
            spec_name="only_str",
            tag_name="div",
            data_model=SemanticTagData,
            allowed_contents=(Contents.Str(),),
        )

        str_contents = ["some text"]
        semantic_tag_contents = [make_semantic_tag(self.soup, self.some_spec)]
        tag_contents = [make_new_tag(self.soup, "span")]

        # ACT & ASSERT
        _validate_semantic_tag_contents(spec_only_str, str_contents)

        with self.assertRaises(InvalidContentsError):
            _validate_semantic_tag_contents(spec_only_str, semantic_tag_contents)

        with self.assertRaises(InvalidContentsError):
            _validate_semantic_tag_contents(spec_only_str, tag_contents)

    def test_only_specs_allowed(self) -> None:
        # ARRANGE
        other_spec = SemanticTagSpec(
            spec_name="other_spec",
            tag_name="span",
            data_model=SemanticTagData,
        )

        spec_only_specs = SemanticTagSpec(
            spec_name="only_specs",
            tag_name="div",
            data_model=SemanticTagData,
            allowed_contents=(Contents.SemanticTag(spec_name=self.some_spec.spec_name),),
        )

        allowed_semantic_tag_contents = [make_semantic_tag(self.soup, self.some_spec)]
        other_semantic_tag_contents = [make_semantic_tag(self.soup, other_spec)]
        str_contents = ["some text"]
        tag_contents = [make_new_tag(self.soup, "span")]

        # ACT & ASSERT
        _validate_semantic_tag_contents(spec_only_specs, allowed_semantic_tag_contents)

        with self.assertRaises(InvalidContentsError):
            _validate_semantic_tag_contents(spec_only_specs, str_contents)

        with self.assertRaises(InvalidContentsError):
            _validate_semantic_tag_contents(spec_only_specs, other_semantic_tag_contents)

        with self.assertRaises(InvalidContentsError):
            _validate_semantic_tag_contents(spec_only_specs, tag_contents)

    def test_only_tags_allowed(self) -> None:
        # ARRANGE
        spec_only_tags = SemanticTagSpec(
            spec_name="only_tags",
            tag_name="div",
            data_model=SemanticTagData,
            allowed_contents=(Contents.Tag(tag_name="span"), Contents.Tag(tag_name="ul")),
        )

        allowed_tag_contents = [make_new_tag(self.soup, "span")]
        str_contents = ["some text"]
        semantic_tag_contents = [make_semantic_tag(self.soup, self.some_spec)]
        wrong_tag_contents = [make_new_tag(self.soup, "ol")]

        # ACT & ASSERT
        _validate_semantic_tag_contents(spec_only_tags, allowed_tag_contents)

        with self.assertRaises(InvalidContentsError):
            _validate_semantic_tag_contents(spec_only_tags, str_contents)

        with self.assertRaises(InvalidContentsError):
            _validate_semantic_tag_contents(spec_only_tags, semantic_tag_contents)

        with self.assertRaises(InvalidContentsError):
            _validate_semantic_tag_contents(spec_only_tags, wrong_tag_contents)

    def test_nothing_allowed(self) -> None:
        # ARRANGE
        spec_nothing = SemanticTagSpec(
            spec_name="nothing",
            tag_name="div",
            data_model=SemanticTagData,
            allowed_contents=(),
        )

        empty_contents: list = []
        str_contents = ["text"]
        semantic_tag_contents = [make_semantic_tag(self.soup, self.some_spec)]
        tag_contents = [make_new_tag(self.soup, "span")]

        # ACT & ASSERT
        _validate_semantic_tag_contents(spec_nothing, empty_contents)

        with self.assertRaises(InvalidContentsError):
            _validate_semantic_tag_contents(spec_nothing, str_contents)

        with self.assertRaises(InvalidContentsError):
            _validate_semantic_tag_contents(spec_nothing, semantic_tag_contents)

        with self.assertRaises(InvalidContentsError):
            _validate_semantic_tag_contents(spec_nothing, tag_contents)

    def test_everything_allowed(self) -> None:
        # ARRANGE
        spec_everything = SemanticTagSpec(
            spec_name="everything",
            tag_name="div",
            data_model=SemanticTagData,
            allowed_contents=(
                Contents.Str(),
                Contents.SemanticTag(spec_name=self.some_spec.spec_name),
                Contents.Tag(tag_name="span"),
            ),
        )

        str_contents = ["text"]
        allowed_semantic_tag_contents = [make_semantic_tag(self.soup, self.some_spec)]
        allowed_tag_contents = [make_new_tag(self.soup, "span")]
        mixed_contents: list[ProtectedTagOrStr] = [
            "text",
            make_semantic_tag(self.soup, self.some_spec),
            make_new_tag(self.soup, "span"),
        ]

        # ACT & ASSERT
        _validate_semantic_tag_contents(spec_everything, str_contents)
        _validate_semantic_tag_contents(spec_everything, allowed_semantic_tag_contents)
        _validate_semantic_tag_contents(spec_everything, allowed_tag_contents)
        _validate_semantic_tag_contents(spec_everything, mixed_contents)

    def test_is_allowed_anywhere(self) -> None:
        # ARRANGE
        spec_is_allowed_anywhere = SemanticTagSpec(
            spec_name="is_allowed_anywhere",
            tag_name="div",
            data_model=SemanticTagData,
            allowed_contents=(),
            is_allowed_anywhere=True,
        )

        semantic_tag_contents = [make_semantic_tag(self.soup, spec_is_allowed_anywhere)]

        # ACT & ASSERT
        _validate_semantic_tag_contents(self.some_spec, semantic_tag_contents)

    def test_tags_allowed_anywhere(self) -> None:
        # ARRANGE
        spec_only_str = SemanticTagSpec(
            spec_name="only_str",
            tag_name="div",
            data_model=SemanticTagData,
            allowed_contents=(Contents.Str(),),
        )

        contents = [
            make_new_tag(self.soup, "b"),
            make_new_tag(self.soup, "i"),
            make_new_tag(self.soup, "u"),
            make_new_tag(self.soup, "strong"),
            make_new_tag(self.soup, "em"),
            make_new_tag(self.soup, "br"),
        ]

        # ACT & ASSERT
        _validate_semantic_tag_contents(spec_only_str, contents)

    def test_tags_allowed_anywhere_but_no_contents_allowed(self) -> None:
        # ARRANGE
        spec_nothing = SemanticTagSpec(
            spec_name="nothing",
            tag_name="div",
            data_model=SemanticTagData,
            allowed_contents=(),
        )

        contents = [
            make_new_tag(self.soup, "b"),
        ]

        # ACT & ASSERT
        with self.assertRaises(InvalidContentsError):
            _validate_semantic_tag_contents(spec_nothing, contents)


class TestValidateTagContents(unittest.TestCase):

    def setUp(self) -> None:
        self.soup = protect_soup(BeautifulSoup("", "html.parser"))

        self.some_spec = SemanticTagSpec(
            spec_name="some_spec",
            tag_name="span",
            data_model=SemanticTagData,
        )

    def test_valid_plain_tags_and_strings(self) -> None:
        # ARRANGE
        div_tag = make_new_tag(self.soup, "div", contents=["text"])
        span_tag = make_new_tag(self.soup, "span", contents=["emphasized"])
        nested_tag = make_new_tag(self.soup, "p")
        nested_tag = replace_children(nested_tag, [span_tag, " more text"])

        # ACT & ASSERT
        _validate_tag_contents(["text"])
        _validate_tag_contents([div_tag, span_tag])
        _validate_tag_contents([div_tag, "text", span_tag])
        _validate_tag_contents([nested_tag])

    def test_invalid_semantic_tag_in_contents(self) -> None:
        # ARRANGE
        semantic_tag = make_semantic_tag(self.soup, self.some_spec)

        # ACT & ASSERT
        with self.assertRaises(InvalidContentsError):
            _validate_tag_contents([semantic_tag])

    def test_invalid_nested_semantic_tag(self) -> None:
        # ARRANGE
        semantic_tag = make_semantic_tag(self.soup, self.some_spec)
        div_tag = make_new_tag(self.soup, "div")
        # Bypass validation by directly manipulating the tag
        unprotect_tag(div_tag).extend(_unprotect_page_elements([semantic_tag]))

        # ACT & ASSERT
        with self.assertRaises(InvalidContentsError):
            _validate_tag_contents(div_tag.contents)

    def test_empty_contents(self) -> None:
        # ARRANGE
        empty_contents: list = []

        # ACT & ASSERT
        _validate_tag_contents(empty_contents)

    def test_is_allowed_anywhere(self) -> None:
        # ARRANGE
        spec_is_allowed_anywhere = SemanticTagSpec(
            spec_name="is_allowed_anywhere",
            tag_name="div",
            data_model=SemanticTagData,
            allowed_contents=(),
            is_allowed_anywhere=True,
        )

        semantic_tag = make_semantic_tag(self.soup, spec_is_allowed_anywhere)

        # ACT & ASSERT
        _validate_tag_contents([semantic_tag])
