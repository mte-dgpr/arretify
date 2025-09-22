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
from typing import Sequence

from bs4 import Tag

from .core import (
    PageElementOrString,
    is_segmentation_tag,
    read_segmentation_tag_name,
    read_segmentation_tag_data,
    make_segmentation_tag,
)


def assert_elements_equal(
    actual: Sequence[PageElementOrString],
    expected: Sequence[PageElementOrString],
    ignore_data_if_omitted: bool = False,
    ignore_text_span_data: bool = False,
    path="",
):
    assert len(actual) == len(
        expected
    ), f"[{path}] Expected {[type(el) for el in expected]} tags, got {[type(el) for el in actual]}"
    for i, (a, e) in enumerate(zip(actual, expected)):
        child_path = f"{path}/{i}"
        if is_segmentation_tag(e):
            assert is_segmentation_tag(
                a, tag_name_in=[read_segmentation_tag_name(e)]
            ), f"[{child_path}] Expected {e}, got {a}"
            # if `ignore_data_if_omitted` is True, test data only
            # if defined in test expectations.
            _assert_data_equal(
                a,
                e,
                ignore_data_if_omitted=ignore_data_if_omitted,
                ignore_text_span_data=ignore_text_span_data,
                path=child_path,
            )
            assert_elements_equal(
                a.contents,
                e.contents,
                path=child_path,
                ignore_data_if_omitted=ignore_data_if_omitted,
                ignore_text_span_data=ignore_text_span_data,
            )
        else:
            assert isinstance(a, str), f"[{child_path}] Expected str, got {a}"
            assert isinstance(e, str)
            assert a == e, f"[{child_path}] Expected {e}, got {a}"


def _assert_data_equal(
    actual: Tag,
    expected: Tag,
    ignore_data_if_omitted: bool = False,
    ignore_text_span_data: bool = False,
    path="",
):
    actual_data = read_segmentation_tag_data(actual)
    expected_data = read_segmentation_tag_data(expected)
    if ignore_data_if_omitted is True and not expected_data:
        return
    if is_segmentation_tag(expected, tag_name_in=["text_span"]) and ignore_text_span_data is True:
        return
    assert actual_data == expected_data, f"[{path}] Expected {expected_data}, got {actual_data}"


def make_text_spans(soup, *lines: str) -> list[Tag]:
    return [
        make_segmentation_tag(
            soup,
            "text_span",
            contents=[line],
            data=dict(start=[0, 0, 0], end=[0, 0, 0]),
        )
        for line in lines
    ]
