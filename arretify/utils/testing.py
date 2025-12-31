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
from typing import Any, Callable, Sequence, TypeVar

from bs4 import BeautifulSoup, Tag

from arretify.settings import Settings
from arretify.types import (
    DocumentContext,
    ProtectedSoup,
    ProtectedTag,
    ProtectedTagOrStr,
    protect_soup,
    unprotect_page_element_or_strings,
    unprotect_soup,
)
from arretify.utils.html import is_tag
from arretify.utils.html_create import make_semantic_tag, make_tag
from arretify.utils.html_semantic import (
    RESERVED_DATA_ATTRIBUTES,
    SemanticTagData,
    SemanticTagSpec,
    get_semantic_tag_data,
    get_semantic_tag_spec,
    is_semantic_tag,
)

PageElementType = TypeVar("PageElementType", bound=Tag | BeautifulSoup)


# -------------------- Helper functions to initialize tests -------------------- #
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


def parse_element(html: str) -> ProtectedTagOrStr:
    """
    Disclaimer : instead of using this function, prefer using
    `make_tag` or `make_semantic_tag` to build your html programmatically when convenient.
    This function is mainly useful when passing a small snippet of html as a string is
    more readable.
    """
    elements = parse_element_list(html)
    if len(elements) != 1:
        raise ValueError("HTML should contain exactly one root element")
    return elements[0]


def parse_element_list(html: str) -> list[ProtectedTagOrStr]:
    """
    Disclaimer : instead of using this function, prefer using
    `make_tag` or `make_semantic_tag` to build your html programmatically when convenient.
    This function is mainly useful when passing a small snippet of html as
    a string is more readable.
    """
    return _normalize_html_multiline_str(html).contents


def _normalize_html_multiline_str(html: str) -> ProtectedSoup:
    """
    Normalize the HTML string by removing indentations and newlines.
    """
    lines: list[str] = html.splitlines()
    cleaned_html: str = ""
    for line in lines:
        cleaned_html += line.lstrip()
    return protect_soup(BeautifulSoup(cleaned_html, features="html.parser"))


# -------------------- Comparison helpers -------------------- #
def assert_data_equal(
    actual_data: SemanticTagData,
    expected_data: SemanticTagData,
    path: str,
) -> None:
    assert actual_data == expected_data, _diff_message(path, "data", expected_data, actual_data)


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
    assert actual_data == expected_data, _diff_message(path, "attrs", expected_data, actual_data)


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
        assert is_semantic_tag(actual), _diff_message(
            path,
            "semantic tag",
            expected,
            actual,
        )
        actual_spec = get_semantic_tag_spec(actual)
        assert actual_spec == expected_spec, _diff_message(
            path, "tag spec", expected_spec, actual_spec
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
        assert is_tag(actual), _diff_message(
            path,
            "tag",
            expected,
            actual,
        )
        assert actual.name == expected.name, _diff_message(
            path, "tag name", expected.name, actual.name
        )
        assert_element_lists_equal(
            actual.contents,
            expected.contents,
            path=path,
            data_assertion_func=data_assertion_func,
        )
    else:
        assert isinstance(actual, type(expected)), _diff_message(
            path,
            "type",
            expected,
            actual,
        )
        assert actual == expected, _diff_message(path, "element", expected, actual)


def assert_element_lists_equal(
    actual: Sequence[ProtectedTagOrStr],
    expected: Sequence[ProtectedTagOrStr],
    path="",
    data_assertion_func: Callable[
        [SemanticTagData, SemanticTagData, str], None
    ] = assert_data_equal,
):
    assert len(actual) == len(expected), _diff_message(path, "elements", expected, actual)

    for i, (actual_child, expected_child) in enumerate(zip(actual, expected)):
        assert_elements_equal(
            actual_child,
            expected_child,
            path=f"{path}/{i}",
            data_assertion_func=data_assertion_func,
        )


def _diff_message(
    path: str,
    label: str,
    expected_value: Any,
    actual_value: Any,
) -> str:
    def _display(value: Any) -> Any:
        if isinstance(value, list):
            return [_display(el) for el in value]
        elif is_tag(value):
            return f"<{value.name}>"
        elif isinstance(value, str):
            return f"'{value[:30]}...'" if len(value) > 30 else f"'{value}'"
        else:
            return value

    path_msg = f"{label.capitalize()} differ at {f'[{path}]' if path else 'root path'}"
    expected_display = _display(expected_value)
    actual_display = _display(actual_value)
    return f"{path_msg}\n" f"Expected :\n{expected_display}\n" f"Actual :\n{actual_display}"


# -------------------- Base class for most html tests  -------------------- #
class BaseTestCaseHtml(unittest.TestCase):
    def setUp(self) -> None:
        super(BaseTestCaseHtml, self).setUp()
        self.context = create_document_context()
        self.soup = self.context.protected_soup

    def make_semantic_tag(self, spec_cls: SemanticTagSpec, **kwargs) -> ProtectedTag:
        """Create a semantic tag with optional reserved data attributes."""
        reserved = kwargs.pop("reserved_data_attrs", {})
        tag = make_semantic_tag(self.soup, spec_cls, **kwargs)
        return _set_reserved_data_attrs(tag, reserved)

    def make_tag(self, tag_name: str, **kwargs) -> ProtectedTag:
        """Create a tag with optional reserved data attributes."""
        reserved = kwargs.pop("reserved_data_attrs", {})
        tag = make_tag(self.soup, tag_name, **kwargs)
        return _set_reserved_data_attrs(tag, reserved)

    def soup_extend(self, contents: list[ProtectedTagOrStr]) -> None:
        unprotect_soup(self.soup).extend(unprotect_page_element_or_strings(contents))


def _set_reserved_data_attrs(
    tag: ProtectedTag,
    reserved_data_attrs: dict[str, str],
) -> ProtectedTag:
    for key, value in reserved_data_attrs.items():
        data_key = f"data-{key}"
        if data_key not in RESERVED_DATA_ATTRIBUTES:
            raise ValueError(f"Attribute '{data_key}' is not a reserved data attribute.")
        tag.attrs[data_key] = value
    return tag
