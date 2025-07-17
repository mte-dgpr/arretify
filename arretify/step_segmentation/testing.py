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
from .core import NodeOrText, is_node


def assert_elements_equal(
    actual: List[NodeOrText],
    expected: List[NodeOrText],
    ignore_data_if_omitted: bool = False,
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
            # if defined is test expectations.
            if ignore_data_if_omitted is False or e.data:
                assert a.data == e.data, f"[{child_path}] Expected {e.data}, got {a.data}"
            assert_elements_equal(
                a.children,
                e.children,
                path=child_path,
                ignore_data_if_omitted=ignore_data_if_omitted,
            )
        else:
            assert isinstance(a, TextSegment), f"[{child_path}] Expected TextSegment, got {a}"
            assert isinstance(e, TextSegment)
            assert _line_column_to_zero(a) == _line_column_to_zero(
                e
            ), f"[{child_path}] Expected {e}, got {a}"


def _line_column_to_zero(text_segment: TextSegment) -> TextSegment:
    return TextSegment(contents=text_segment.contents, start=(0, 0, 0), end=(0, 0, 0))


def _l(*raw_lines: str, page_index: int = 0) -> List[TextSegment]:
    return initialize_page("\n".join(raw_lines), page_index)
