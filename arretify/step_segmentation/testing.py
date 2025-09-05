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
from typing import List

from arretify.parsing_utils.source_mapping import initialize_page
from arretify.types import TextSegment
from .core import NodeOrText, is_node, Node


def assert_elements_equal(
    actual: List[NodeOrText],
    expected: List[NodeOrText],
    ignore_data_if_omitted: bool = False,
    ignore_text_span_data: bool = False,
    path="",
):
    assert len(actual) == len(
        expected
    ), f"[{path}] Expected {[type(el) for el in expected]} nodes, got {[type(el) for el in actual]}"
    for i, (a, e) in enumerate(zip(actual, expected)):
        child_path = f"{path}/{i}"
        if is_node(e):
            assert is_node(a, type_in=[e.type]), f"[{child_path}] Expected {e}, got {a}"
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
                a.children,
                e.children,
                path=child_path,
                ignore_data_if_omitted=ignore_data_if_omitted,
                ignore_text_span_data=ignore_text_span_data,
            )
        else:
            assert isinstance(a, TextSegment), f"[{child_path}] Expected TextSegment, got {a}"
            assert isinstance(e, TextSegment)
            assert _line_column_to_zero(a) == _line_column_to_zero(
                e
            ), f"[{child_path}] Expected {e}, got {a}"


def _assert_data_equal(
    actual: Node,
    expected: Node,
    ignore_data_if_omitted: bool = False,
    ignore_text_span_data: bool = False,
    path="",
):
    if ignore_data_if_omitted is True and not expected.data:
        return
    if expected.type == "text_span" and ignore_text_span_data is True:
        return
    assert actual.data == expected.data, f"[{path}] Expected {expected.data}, got {actual.data}"


def _line_column_to_zero(text_segment: TextSegment) -> TextSegment:
    return TextSegment(contents=text_segment.contents, start=(0, 0, 0), end=(0, 0, 0))


def _l(*raw_lines: str, page_index: int = 0) -> List[TextSegment]:
    return initialize_page("\n".join(raw_lines), page_index)


def make_text_spans(*raw_lines: str, page_index: int = 0) -> List[Node]:
    return [
        Node(
            type="text_span",
            children=[text_segment],
            data=dict(start=text_segment.start, end=text_segment.end),
        )
        for text_segment in initialize_page("\n".join(raw_lines), page_index)
    ]
