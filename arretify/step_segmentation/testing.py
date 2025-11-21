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

from arretify.step_segmentation.semantic_tag_specs import (
    TextSpanSegmentationData,
    TextSpanSegmentationSpec,
)
from arretify.types import ProtectedTag, ProtectedTagOrStr
from arretify.utils.html import is_tag
from arretify.utils.html_create import make_semantic_tag
from arretify.utils.html_semantic import (
    get_semantic_tag_data,
    get_semantic_tag_spec,
    is_semantic_tag,
)


def assert_elements_equal(
    actual: Sequence[ProtectedTagOrStr],
    expected: Sequence[ProtectedTagOrStr],
    ignore_data_if_omitted: bool = False,
    ignore_text_span_data: bool = False,
    path="",
):
    assert len(actual) == len(
        expected
    ), f"[{path}] Expected {[type(el) for el in expected]} tags, got {[type(el) for el in actual]}"
    for i, (a, e) in enumerate(zip(actual, expected)):
        child_path = f"{path}/{i}"
        if is_semantic_tag(e):
            assert is_semantic_tag(a), f"[{child_path}] Expected semantic tag, got : {a}"
            assert get_semantic_tag_spec(a) == get_semantic_tag_spec(e), (
                f"[{child_path}] Expected tag spec '{get_semantic_tag_spec(e)}', "
                f"got '{get_semantic_tag_spec(a)}'"
            )
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
        elif is_tag(a):
            assert is_tag(e), f"[{child_path}] Expected Tag, got : {e}"
            assert a.name == e.name, f"[{child_path}] Expected tag name '{e.name}', got '{a.name}'"
            assert_elements_equal(
                a.contents,
                e.contents,
                path=child_path,
                ignore_data_if_omitted=ignore_data_if_omitted,
                ignore_text_span_data=ignore_text_span_data,
            )
        else:
            assert isinstance(a, type(e)), f"[{child_path}] Expected {type(e)}, got {type(a)}"
            assert a == e, f"[{child_path}] Expected {e}, got {a}"


def _assert_data_equal(
    actual: ProtectedTag,
    expected: ProtectedTag,
    ignore_data_if_omitted: bool = False,
    ignore_text_span_data: bool = False,
    path="",
):
    spec = get_semantic_tag_spec(expected)
    actual_data = get_semantic_tag_data(spec, actual)
    expected_data = get_semantic_tag_data(spec, expected)
    if ignore_data_if_omitted is True and not expected_data:
        return
    if (
        is_semantic_tag(expected, spec_in=[TextSpanSegmentationSpec])
        and ignore_text_span_data is True
    ):
        return
    assert actual_data == expected_data, f"[{path}] Expected {expected_data}, got {actual_data}"


def make_text_spans(soup, *lines: str) -> list[ProtectedTag]:
    return [
        make_semantic_tag(
            soup,
            TextSpanSegmentationSpec,
            contents=[line],
            data=TextSpanSegmentationData(start=[0, 0, 0], end=[0, 0, 0]),
        )
        for line in lines
    ]
