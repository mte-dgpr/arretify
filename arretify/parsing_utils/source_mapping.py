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
