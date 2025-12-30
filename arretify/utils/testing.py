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
import re
import unittest
from functools import partial
from typing import Callable, Sequence, TypeVar

from bs4 import BeautifulSoup, NavigableString, Tag

from arretify.settings import Settings
from arretify.types import DocumentContext, ProtectedTag, ProtectedTagOrStr, unprotect_soup
from arretify.utils.html import is_tag
from arretify.utils.html_create import make_semantic_tag, make_tag
from arretify.utils.html_semantic import (
    RESERVED_DATA_ATTRIBUTES,
    SemanticTagData,
    get_semantic_tag_data,
    get_semantic_tag_spec,
    is_semantic_tag,
)

_INLINE_TAGS = [
    "a",
    "abbr",
    "acronym",
    "b",
    "bdo",
    "big",
    "cite",
    "code",
    "em",
    "i",
    "kbd",
    "mark",
    "q",
    "samp",
    "small",
    "span",
    "strong",
    "sub",
    "sup",
    "time",
    "u",
    "var",
    "wbr",
    "br",
    "img",
    "hr",
    "input",
    "select",
    "textarea",
    "button",
    "label",
]
_INDENTATION_PATTERN = re.compile(r"\n[\s\t]{2,}")
_NO_CONTENT = re.compile(r"^[\s]*$")

PageElementType = TypeVar("PageElementType", bound=Tag | BeautifulSoup)


def create_document_context(
    html: str = "",
) -> DocumentContext:
    return DocumentContext(
        soup=BeautifulSoup(html, features="html.parser"),
        input_path=None,
        pdf=None,
        pages=[],
        settings=create_settings(),
        legifrance_client=None,
        eurlex_client=None,
    )


def create_settings() -> Settings:
    return Settings(
        tmp_dir="./tmp",
        env="development",
        legifrance_client_id=None,
        legifrance_client_secret=None,
        eurlex_web_service_username=None,
        eurlex_web_service_password=None,
    )


def normalized_soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(
        normalized_html_str(html),
        features="html.parser",
    )


def assert_html_list_equal(
    actual: Sequence[ProtectedTagOrStr],
    expected: Sequence[ProtectedTagOrStr],
) -> None:
    """
    Assert that two lists of HTML strings are equal after normalization.
    """
    assert len(actual) == len(expected)
    for i, (actual_html, expected_html) in enumerate(
        zip(_normalize_element_list(actual), _normalize_element_list(expected))
    ):
        assert actual_html == expected_html, (
            f"Elements in position {i} are not equal :"
            f"\nACTUAL:\n{actual_html}\nEXPECTED:\n{expected_html}"
        )


def _normalize_element_list(
    html_list: Sequence[ProtectedTagOrStr],
) -> list[ProtectedTagOrStr]:
    return [
        normalized_html_str(str(element)) if is_tag(element) else str(element)
        for element in html_list
    ]


def normalized_html_str(html: str) -> str:
    """
    Normalize the HTML string by removing unnecessary whitespace and
    indentation, and ensuring consistent formatting.
    Allows to write tests with a multiline HTML strings. For example :

        <div>
            <span>bli</span>
            bla
            blo
        </div>

    becomes :

        <div><span>bli</span> bla blo</div>
    """
    return str(
        _normalize_tag(
            BeautifulSoup(
                html,
                features="html.parser",
            )
        )
    )


def _normalize_string(nav_string: NavigableString) -> str | None:
    strip_chars = " \n\t"
    string = str(nav_string)
    string = _INDENTATION_PATTERN.sub(" ", string)

    if _NO_CONTENT.match(string):
        return None

    def _ensure_space_right(string: str) -> str:
        if string and string[-1] != " ":
            return string + " "
        return string

    def _ensure_space_left(string: str) -> str:
        if string and string[0] != " ":
            return " " + string
        return string

    if nav_string.previous_sibling is None:
        string = string.lstrip(strip_chars)
    elif isinstance(nav_string.previous_sibling, Tag):
        if nav_string.previous_sibling.name in _INLINE_TAGS:
            string = _ensure_space_left(string)
        else:
            string = string.lstrip(strip_chars)

    if nav_string.next_sibling is None:
        string = string.rstrip(strip_chars)
    elif isinstance(nav_string.next_sibling, Tag):
        if nav_string.next_sibling.name in _INLINE_TAGS:
            string = _ensure_space_right(string)
        else:
            string = string.rstrip(strip_chars)
    elif isinstance(nav_string.next_sibling, str):
        string = _ensure_space_right(string)

    return string


def _normalize_tag(tag: PageElementType) -> PageElementType:
    new_children: list[Tag | str] = []
    for child in tag.contents:
        if isinstance(child, NavigableString):
            normalized_string = _normalize_string(child)
            if normalized_string is not None:
                new_children.append(normalized_string)
        elif isinstance(child, (Tag, BeautifulSoup)):
            new_children.append(_normalize_tag(child))
    tag.clear()
    tag.extend(new_children)
    return tag


def assert_data_equal(
    actual_data: SemanticTagData,
    expected_data: SemanticTagData,
    path: str,
) -> None:
    assert (
        actual_data == expected_data
    ), f"{_path_str(path)}Expected data :\n{expected_data}\nActual data :\n{actual_data}"


def assert_attrs_equal(
    actual: ProtectedTag,
    expected: ProtectedTag,
    path: str,
) -> None:
    actual_data = dict(actual.attrs)
    expected_data = dict(expected.attrs)
    # Clean data- attributes which are tested separately in data equality tests
    for data in [actual_data, expected_data]:
        for key in list(data.keys()):
            if key.startswith("data-") and key not in RESERVED_DATA_ATTRIBUTES:
                data.pop(key)
    assert (
        actual_data == expected_data
    ), f"{_path_str(path)}Expected attrs :\n{expected_data}\nActual attrs :\n{actual_data}"


def assert_elements_equal(
    actual: ProtectedTagOrStr,
    expected: ProtectedTagOrStr,
    path="",
    data_assertion_func: Callable[
        [SemanticTagData, SemanticTagData, str], None
    ] = assert_data_equal,
) -> None:
    if is_tag(expected) and is_tag(actual):
        assert_attrs_equal(
            actual,
            expected,
            path,
        )

    if is_semantic_tag(expected):
        # Checking actual child is also a semantic tag and has the right spec
        expected_spec = get_semantic_tag_spec(expected)
        assert is_semantic_tag(actual), f"{_path_str(path)}Expected semantic tag, got : {actual}"
        actual_spec = get_semantic_tag_spec(actual)
        assert actual_spec == expected_spec, (
            f"{_path_str(path)}Expected tag spec '{expected_spec}', " f"got '{actual_spec}'"
        )

        # Checking data equality
        actual_data = get_semantic_tag_data(expected_spec, actual)
        expected_data = get_semantic_tag_data(expected_spec, expected)
        data_assertion_func(
            actual_data,
            expected_data,
            path,
        )

        # Recursively checking children
        assert_element_lists_equal(
            actual.contents,
            expected.contents,
            path=path,
            data_assertion_func=data_assertion_func,
        )
    elif is_tag(expected):
        assert is_tag(expected), f"{_path_str(path)}Expected Tag, got : {expected}"
        assert actual.name == expected.name, (
            f"{_path_str(path)}Expected tag name '{expected.name}', " f"got '{actual.name}'"
        )
        assert_element_lists_equal(
            actual.contents,
            expected.contents,
            path=path,
            data_assertion_func=data_assertion_func,
        )
    else:
        assert isinstance(
            actual, type(expected)
        ), f"{_path_str(path)}Expected {type(expected)}, got {type(actual)}"
        assert actual == expected, f"{_path_str(path)}Expected {expected}, got {actual}"


def assert_element_lists_equal(
    actual: Sequence[ProtectedTagOrStr],
    expected: Sequence[ProtectedTagOrStr],
    path="",
    data_assertion_func: Callable[
        [SemanticTagData, SemanticTagData, str], None
    ] = assert_data_equal,
):
    assert len(actual) == len(expected), (
        f"{_path_str(path)}Expected {[type(el) for el in expected]} tags, "
        f"got {[type(el) for el in actual]}"
    )

    for i, (actual_child, expected_child) in enumerate(zip(actual, expected)):
        assert_elements_equal(
            actual_child,
            expected_child,
            path=f"{path}/{i}",
            data_assertion_func=data_assertion_func,
        )


def _path_str(path: str) -> str:
    return f"[{path}] " if path else ""


class BaseTestCaseHtml(unittest.TestCase):
    def setUp(self) -> None:
        super(BaseTestCaseHtml, self).setUp()
        self.context = create_document_context()
        self.soup = self.context.protected_soup

        def _make_semantic_tag(
            soup: BeautifulSoup,
            spec_cls: type,
            contents: list[ProtectedTagOrStr] = [],
            data: SemanticTagData | None = None,
            attrs: dict[str, str] = {},
            reserved_data_attrs: dict[str, str] = {},
        ) -> ProtectedTag:
            """
            Helper to create a semantic tag with reserved data attributes.
            """
            tag = make_semantic_tag(
                soup,
                spec_cls,
                contents=contents,
                data=data,
                attrs=attrs,
            )
            for key, value in reserved_data_attrs.items():
                data_key = f"data-{key}"
                if data_key not in RESERVED_DATA_ATTRIBUTES:
                    raise ValueError(f"Attribute '{data_key}' is not a reserved data attribute.")
                tag.attrs[data_key] = value
            return tag

        self.make_semantic_tag = partial(_make_semantic_tag, self.soup)
        self.make_tag = partial(make_tag, self.soup)
        self.soup_extend = unprotect_soup(self.soup).extend
