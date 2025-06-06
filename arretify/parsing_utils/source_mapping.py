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


from arretify.types import TextSegments, TextSegment


def initialize_lines(lines: List[str]) -> TextSegments:
    return [
        TextSegment(contents=line, start=(i, 0), end=(i, len(line))) for i, line in enumerate(lines)
    ]


def apply_to_segment(segment: TextSegment, func: Callable[[str], str]) -> TextSegment:
    return TextSegment(
        contents=func(segment.contents),
        start=segment.start,
        end=segment.end,
    )


def combine_text_segments(combined_contents: str, segments: TextSegments) -> TextSegment:
    return TextSegment(
        contents=combined_contents,
        start=min(segments, key=lambda segment: segment.start).start,
        end=max(segments, key=lambda segment: segment.end).end,
    )


def text_segments_to_str(segments: TextSegments) -> List[str]:
    return [segment.contents for segment in segments]
