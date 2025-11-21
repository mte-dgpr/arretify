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
from typing import Callable, Sequence, TypeVar

from bs4 import BeautifulSoup, NavigableString, Tag

from arretify.settings import Settings
from arretify.types import DocumentContext, ProtectedTag, ProtectedTagOrStr
from arretify.utils.html import is_tag

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


def make_testing_function_for_single_tag(
    process_function: Callable[[DocumentContext, ProtectedTag], None],
) -> Callable[[str], str]:
    def _testing_function(string: str, css_selector: str | None = None) -> str:
        document_context = create_document_context(normalized_html_str(string))

        tag_list: list[ProtectedTagOrStr]
        if css_selector is None:
            tag_list = list(document_context.protected_soup.contents)
        else:
            tag_list = list(document_context.protected_soup.select(css_selector))
        tag_list = [tag for tag in tag_list if is_tag(tag)]

        if len(tag_list) != 1:
            raise ValueError("One and only one tag must be found")

        if not is_tag(tag_list[0]):
            raise ValueError("No tag found")

        tag = tag_list[0]
        process_function(document_context, tag)
        return normalized_html_str(str(tag))

    return _testing_function


def make_testing_function_for_children_list(
    process_function: Callable[
        [DocumentContext, Sequence[ProtectedTagOrStr]],
        Sequence[ProtectedTagOrStr],
    ],
) -> Callable[[str], str]:
    def _testing_function(string: str):
        document_context = create_document_context(normalized_html_str(string))
        elements = list(
            process_function(document_context, list(document_context.protected_soup.contents))
        )
        return _normalize_element_list(elements)

    return _testing_function


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
