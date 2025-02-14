from typing import List, Callable, Tuple
from dataclasses import dataclass

from bs4 import PageElement

from bench_convertisseur_xml.types import LineColumn


@dataclass(frozen=True)
class _SegmentBase:
    start: LineColumn
    end: LineColumn


@dataclass(frozen=True)
class TextSegment(_SegmentBase):
    contents: str

TextSegments = List[TextSegment]


def initialize_lines(lines: List[str]) -> TextSegments:
    return [
        TextSegment(
            contents=line, 
            start=(i, 0), 
            end=(i, len(line))
        ) for i, line in enumerate(lines)
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