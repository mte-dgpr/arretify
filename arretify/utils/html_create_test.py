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

from arretify.types import (
    ProtectedSoup,
    ProtectedTag,
    ProtectedTagOrStr,
    protect_soup,
    unprotect_tag,
)
from arretify.utils.html import set_non_data_attributes
from arretify.utils.html_semantic import (
    Contents,
    SemanticTagData,
    SemanticTagSpec,
    create_semantic_tag_spec_no_data,
)
from arretify.utils.html_semantic_test import SemanticTagDataTestCase

from .html_create import (
    InvalidContentsError,
    _make_tag,
    _unprotect_page_elements,
    _validate_tag_contents,
    make_semantic_tag,
    make_tag,
    replace_contents,
    upgrade_to_semantic_tag,
    validate_semantic_tag_contents,
)


class TestMakeNewTag(unittest.TestCase):

    def setUp(self):
        self.soup = BeautifulSoup("", features="html.parser")

    def test_with_contents_iterator(self):
        # ARRANGE
        contents = (f"Item {i}" for i in range(3))

        # ACT
        tag = make_tag(self.soup, "ul", contents=contents)

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
            make_tag(self.soup, "p", contents=contents)

    def test_attrs_parameter(self):
        # ACT
        tag = make_tag(
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
            make_tag(
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
            make_tag(self.soup, "span", contents=["text"]),
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

    def test_with_other_semantic_tags_in_contents(self):
        # ARRANGE
        child_spec = create_semantic_tag_spec_no_data(
            spec_name="child_spec",
            tag_name="span",
            allowed_contents=(Contents.Str(),),
        )
        parent_spec = create_semantic_tag_spec_no_data(
            spec_name="parent_spec",
            tag_name="div",
            allowed_contents=(Contents.SemanticTag(child_spec.spec_name),),
        )
        contents = [
            make_semantic_tag(self.soup, child_spec, contents=["child text"]),
        ]

        # ACT
        tag = make_semantic_tag(self.soup, parent_spec, contents=contents)

        # ASSERT
        assert str(tag) == (
            '<div data-spec="parent_spec">'
            '<span data-spec="child_spec">child text</span>'
            "</div>"
        )

    def test_callable_tag_name(self) -> None:
        """
        Test tag generation with callable tag_name in SemanticTagSpec.
        """

        # ARRANGE
        class CustomData(SemanticTagData):
            value: str

        def _tag_name_func(soup: ProtectedSoup, data: CustomData) -> ProtectedTag:
            tag = _make_tag(soup, "span")
            set_non_data_attributes(tag, {"alt": data.value})
            return tag

        spec = SemanticTagSpec(
            spec_name="span_spec",
            tag_name=_tag_name_func,
            data_model=CustomData,
            allowed_contents=(Contents.Str(),),
        )

        # ACT
        tag = make_semantic_tag(self.soup, spec, data=CustomData(value="some text"))

        # ASSERT
        assert (
            str(tag) == '<span alt="some text" data-spec="span_spec" data-value="some text"></span>'
        )

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
        plain_tag = make_tag(self.soup, "span", contents=["text"])

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

        self.other_spec = SemanticTagSpec(
            spec_name="other_spec",
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
        tag_contents = [make_tag(self.soup, "span")]

        # ACT & ASSERT
        validate_semantic_tag_contents(spec_only_str, str_contents)

        with self.assertRaises(InvalidContentsError):
            validate_semantic_tag_contents(spec_only_str, semantic_tag_contents)

        with self.assertRaises(InvalidContentsError):
            validate_semantic_tag_contents(spec_only_str, tag_contents)

    def test_only_specs_allowed(self) -> None:
        # ARRANGE
        spec_only_specs = SemanticTagSpec(
            spec_name="only_specs",
            tag_name="div",
            data_model=SemanticTagData,
            allowed_contents=(Contents.SemanticTag(spec_name=self.some_spec.spec_name),),
        )

        allowed_semantic_tag_contents = [make_semantic_tag(self.soup, self.some_spec)]
        other_semantic_tag_contents = [make_semantic_tag(self.soup, self.other_spec)]
        str_contents = ["some text"]
        tag_contents = [make_tag(self.soup, "span")]

        # ACT & ASSERT
        validate_semantic_tag_contents(spec_only_specs, allowed_semantic_tag_contents)

        with self.assertRaises(InvalidContentsError):
            validate_semantic_tag_contents(spec_only_specs, str_contents)

        with self.assertRaises(InvalidContentsError):
            validate_semantic_tag_contents(spec_only_specs, other_semantic_tag_contents)

        with self.assertRaises(InvalidContentsError):
            validate_semantic_tag_contents(spec_only_specs, tag_contents)

    def test_only_tags_allowed(self) -> None:
        # ARRANGE
        spec_only_tags = SemanticTagSpec(
            spec_name="only_tags",
            tag_name="div",
            data_model=SemanticTagData,
            allowed_contents=(Contents.Tag(tag_name="span"), Contents.Tag(tag_name="ul")),
        )

        allowed_tag_contents = [make_tag(self.soup, "span")]
        str_contents = ["some text"]
        semantic_tag_contents = [make_semantic_tag(self.soup, self.some_spec)]
        wrong_tag_contents = [make_tag(self.soup, "ol")]

        # ACT & ASSERT
        validate_semantic_tag_contents(spec_only_tags, allowed_tag_contents)

        with self.assertRaises(InvalidContentsError):
            validate_semantic_tag_contents(spec_only_tags, str_contents)

        with self.assertRaises(InvalidContentsError):
            validate_semantic_tag_contents(spec_only_tags, semantic_tag_contents)

        with self.assertRaises(InvalidContentsError):
            validate_semantic_tag_contents(spec_only_tags, wrong_tag_contents)

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
        tag_contents = [make_tag(self.soup, "span")]

        # ACT & ASSERT
        validate_semantic_tag_contents(spec_nothing, empty_contents)

        with self.assertRaises(InvalidContentsError):
            validate_semantic_tag_contents(spec_nothing, str_contents)

        with self.assertRaises(InvalidContentsError):
            validate_semantic_tag_contents(spec_nothing, semantic_tag_contents)

        with self.assertRaises(InvalidContentsError):
            validate_semantic_tag_contents(spec_nothing, tag_contents)

    def test_everything_allowed(self) -> None:
        # ARRANGE
        spec_everything = SemanticTagSpec(
            spec_name="everything",
            tag_name="div",
            data_model=SemanticTagData,
            allowed_contents=None,
        )

        str_contents = ["text"]
        allowed_semantic_tag_contents = [make_semantic_tag(self.soup, self.some_spec)]
        allowed_tag_contents = [make_tag(self.soup, "span")]
        mixed_contents: list[ProtectedTagOrStr] = [
            "text",
            make_semantic_tag(self.soup, self.some_spec),
            make_tag(self.soup, "span"),
        ]

        # ACT & ASSERT
        validate_semantic_tag_contents(spec_everything, str_contents)
        validate_semantic_tag_contents(spec_everything, allowed_semantic_tag_contents)
        validate_semantic_tag_contents(spec_everything, allowed_tag_contents)
        validate_semantic_tag_contents(spec_everything, mixed_contents)

    def test_semantic_tag_is_allowed_anywhere(self) -> None:
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
        validate_semantic_tag_contents(self.some_spec, semantic_tag_contents)

    def test_tags_allowed_anywhere(self) -> None:
        # ARRANGE
        spec_only_str = SemanticTagSpec(
            spec_name="only_str",
            tag_name="div",
            data_model=SemanticTagData,
            allowed_contents=(Contents.Str(),),
        )

        contents = [
            make_tag(self.soup, "b"),
            make_tag(self.soup, "i"),
            make_tag(self.soup, "u"),
            make_tag(self.soup, "strong"),
            make_tag(self.soup, "em"),
            make_tag(self.soup, "br"),
        ]

        # ACT & ASSERT
        validate_semantic_tag_contents(spec_only_str, contents)

    def test_tags_allowed_anywhere_but_no_contents_allowed(self) -> None:
        # ARRANGE
        spec_nothing = SemanticTagSpec(
            spec_name="nothing",
            tag_name="div",
            data_model=SemanticTagData,
            allowed_contents=(),
        )

        contents = [
            make_tag(self.soup, "b"),
        ]

        # ACT & ASSERT
        with self.assertRaises(InvalidContentsError):
            validate_semantic_tag_contents(spec_nothing, contents)

    def test_errors_list(self):
        # ARRANGE
        spec_allowing_some_stuff = SemanticTagSpec(
            spec_name="spec_allowing_some_stuff",
            tag_name="div",
            data_model=SemanticTagData,
            allowed_contents=(
                Contents.SemanticTag(spec_name=self.some_spec.spec_name),
                Contents.Tag(tag_name="span"),
            ),
        )

        contents = [
            make_tag(self.soup, "span"),  # Allowed
            make_tag(self.soup, "div"),  # Not allowed
            make_semantic_tag(self.soup, self.some_spec),  # Allowed
            make_semantic_tag(self.soup, self.other_spec),  # Not allowed
            "bla",  # Not allowed
            42,  # type: ignore
        ]

        # ACT & ASSERT
        with self.assertRaises(InvalidContentsError) as context:
            validate_semantic_tag_contents(spec_allowing_some_stuff, contents)

        errors = context.exception.errors
        assert len(errors) == 4
        assert errors[0] == (1, "tag div not allowed")
        assert errors[1] == (3, "semantic tag other_spec not allowed")
        assert errors[2] == (4, "string content not allowed")
        assert errors[3] == (5, "invalid content type <class 'int'>")


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
        div_tag = make_tag(self.soup, "div", contents=["text"])
        span_tag = make_tag(self.soup, "span", contents=["emphasized"])
        nested_tag = make_tag(self.soup, "p")
        nested_tag = replace_contents(nested_tag, [span_tag, " more text"])

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
        div_tag = make_tag(self.soup, "div")
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

    def test_errors_list(self) -> None:
        # ARRANGE
        contents: list[ProtectedTagOrStr] = [
            "valid string",
            make_semantic_tag(self.soup, self.some_spec),
            make_tag(self.soup, "div"),
            make_semantic_tag(self.soup, self.some_spec),
            "other string",
            42,  # type: ignore
        ]

        # ACT & ASSERT
        with self.assertRaises(InvalidContentsError) as context:
            _validate_tag_contents(contents)

        errors = context.exception.errors
        assert len(errors) == 3
        assert errors[0] == (1, "semantic tag some_spec not allowed")
        assert errors[1] == (3, "semantic tag some_spec not allowed")
        assert errors[2] == (5, "invalid content type <class 'int'>")


class TestEdgesCases(unittest.TestCase):
    """
    It is really easy to shoot oneself in the foot when mixing up
    iterations over elements and modifying the document structure.
    """

    def test_keeps_unchanged_contents_references(self):
        """
        Consider the following example:

            >>> soup = BeautifulSoup("<div class="some-class"><span>to keep</span></div>", features="html.parser")
            >>> for tag in soup.select(".some-class, .some-class *"):
            ...     # first process the `<div>` tag, and then the `<span>` tag inside it.
            ...     replace_contents(tag, clone_contents(tag.contents))

        If `replace_contents` is implemented by cloning its new contents before inserting them,
        processing the div tag will cause the span tag to be removed from the document.

        When the loop continues to the span tag, it will no longer be in the document,
        causing errors or unexpected behavior.
        """  # noqa: E501
        # ARRANGE
        soup = BeautifulSoup("", features="html.parser")
        child = make_tag(soup, "span", contents=["to keep"])
        tag = make_tag(soup, "div", contents=[child])

        new_contents = [
            "new ",
            make_tag(soup, "span", contents=["content"]),
            child,
        ]

        # ACT
        updated_tag = replace_contents(tag, new_contents)

        # ASSERT
        assert updated_tag is tag
        assert str(updated_tag) == "<div>new <span>content</span><span>to keep</span></div>"
        assert child.parent is updated_tag

    def test_make_new_tag_from_dynamically_mutated_list_of_children(self):
        """
        Consider the following example:

            >>> soup = BeautifulSoup("<span>bla</span><span>blo</span>", features="html.parser")
            >>> elements = []
            >>> for child in soup.contents:
            ...     # Wrap each child in a new <div> tag
            ...     elements.append(make_new_tag(soup, "div", contents=[child]))

        When passing an element as `contents` to `make_new_tag`, that element
        is moved to another parent during the call. This means that `soup.contents`
        is being mutated during the iteration, which can lead to unexpected behavior.
        """
        # Arrange
        soup = BeautifulSoup("<span>bla</span><span>blo</span>", features="html.parser")

        # Act
        elements = []
        for child in soup.contents:
            elements.append(make_tag(soup, "div", contents=[child]))

        # Assert
        assert len(elements) == 2
        assert str(elements[0]) == "<div><span>bla</span></div>"
        assert str(elements[1]) == "<div><span>blo</span></div>"
