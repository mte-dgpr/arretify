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
from typing import List, Callable
from dataclasses import replace as dataclass_replace


from arretify.types import TextSegment


def initialize_page(page_text: str, page_index: int) -> List[TextSegment]:
    return [
        TextSegment(contents=line, start=(page_index, i, 0), end=(page_index, i, len(line)))
        for i, line in enumerate(page_text.split("\n"))
    ]


def initialize_pages(page_texts: List[str]) -> List[TextSegment]:
    return [
        line for i, page_text in enumerate(page_texts) for line in initialize_page(page_text, i)
    ]


def apply_to_segment(segment: TextSegment, func: Callable[[str], str]) -> TextSegment:
    return dataclass_replace(
        segment,
        contents=func(segment.contents),
    )
