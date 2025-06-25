from typing import Callable, Iterator, Iterable, List, TypeGuard, Dict, Any
from dataclasses import dataclass, field

from arretify.types import TextSegments, TextSegment, DataElementDataDict


ElementFlow = Iterable[TextSegments | "Element"]
Probe = Callable[[TextSegments, int], bool]


@dataclass(frozen=True)
class Element:
    name: str
    contents: List[TextSegments | "Element"]
    data: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        # Make sure contents are a list and not an iterator 
        if not isinstance(self.contents, list):
            self.contents = list(self.contents)


def flat_map_element_flow(
    elements: ElementFlow,
    map_func: Callable[[TextSegments], ElementFlow],
) -> List[TextSegments | Element]:
    output: List[TextSegments | Element] = []
    for element in elements:
        if isinstance(element, Element):
            output.append(element)
        else:
            output.extend(map_func(element))
    return output


def assert_single_text_segments(element: Element) -> TextSegments:
    if len(element.contents) != 1 or isinstance(element.contents[0], Element):
        raise ValueError(
            f"Element '{element.name}' must contain exactly one TextSegments, "
            f"but found {len(element.contents)} elements."
        )
    return element.contents[0]


def assert_single_text_segment(element: Element) -> TextSegment:
    text_segments = assert_single_text_segments(element)
    if len(text_segments) != 1:
        raise ValueError(
            f"Element '{element.name}' must contain exactly one line, "
            f"but found {len(text_segments)} lines."
        )
    return text_segments[0]


def is_element(element: Element | TextSegments, name: str | None=None) -> TypeGuard[Element]:
    if not isinstance(element, Element):
        return False

    if name is not None:
        return element.name == name
    return True