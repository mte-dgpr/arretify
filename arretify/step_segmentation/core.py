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
from typing import Iterator, Sequence, cast

from arretify.parsing_utils.patterns import is_continuing_sentence
from arretify.regex_utils import MatchProxy, PatternProxy
from arretify.semantic_tag_specs import AddressSpec, PageFooterSpec, PageSeparatorSpec
from arretify.step_segmentation.semantic_tag_specs import (
    TextSpanSegmentationData,
    TextSpanSegmentationSpec,
)
from arretify.types import DocumentContext, ProtectedTag, ProtectedTagOrStr
from arretify.utils.functional import iter_func_to_list
from arretify.utils.html_create import make_semantic_tag
from arretify.utils.html_semantic import SemanticTagSpec, get_semantic_tag_data, is_semantic_tag
from arretify.utils.split_merge import (
    Probe,
    RawSplit,
    SplitMatch,
    Splitter,
    make_single_line_splitter,
    make_while_splitter,
    merge_splitted_elements,
    split_before_match,
    split_elements,
)
from arretify.utils.strings import merge_strings

TRANSPARENT_TAG_SPECS: list[SemanticTagSpec] = [PageSeparatorSpec, PageFooterSpec]
"""
List of tag names that are considered transparent for text extraction purposes.
"""

_STR_TAG_SPECS: list[SemanticTagSpec] = [AddressSpec]
"""
List of tag names that contains specific bits of text information inside a text_span.
"""


def pick_if_transparent_tag_followed_by_match(
    is_matching: Probe[ProtectedTagOrStr],
) -> Probe[ProtectedTagOrStr]:
    """
    Builds a function that returns True for a transparent tag,
    only if it is followed by an element that matches the provided `is_matching` function.
    For other elements, it will return the result of the `is_matching` function directly.

    For example :

    >>> elements = [
    ...     "Hello",
    ...     <page_separator />,
    ...     "World",
    ...     <page_separator />,
    ...     <other_tag />,
    ... ]
    >>> def is_string(elements: Sequence[ProtectedTagOrStr], index: int) -> bool:
    ...     return isinstance(elements[index], str)
    >>> probe = pick_if_transparent_tag_followed_by_match(is_string)
    >>> probe(elements, 0) # -> directly calls `is_string`
    True
    >>> probe(elements, 1) # -> calls `is_string` on the next element
    True
    >>> probe(elements, 3) # -> calls `is_string` on the next element
    False
    """

    def _probe(elements: Sequence[ProtectedTagOrStr], index: int) -> bool:
        for next_index, next_element in enumerate(elements[index:], start=index):
            if is_semantic_tag(next_element, spec_in=TRANSPARENT_TAG_SPECS):
                continue
            else:
                return is_matching(elements, next_index)
        return False

    return _probe


def pick_text_spans(
    probe: Probe[ProtectedTagOrStr],
) -> Probe[ProtectedTagOrStr]:
    def _probe(elements: Sequence[ProtectedTagOrStr], index: int) -> bool:
        element = elements[index]
        if is_semantic_tag(element, spec_in=[TextSpanSegmentationSpec]):
            return probe(elements, index)
        return False

    return _probe


def pick_str(
    probe: Probe[ProtectedTagOrStr],
) -> Probe[ProtectedTagOrStr]:
    def _probe(elements: Sequence[ProtectedTagOrStr], index: int) -> bool:
        element = elements[index]
        if isinstance(element, str):
            return probe(elements, index)
        return False

    return _probe


def make_probe_from_pattern_proxy(
    pattern: PatternProxy, use_search: bool = False
) -> Probe[ProtectedTagOrStr]:
    def _probe(elements: Sequence[ProtectedTagOrStr], index: int) -> bool:
        string = get_string(elements[index])
        if use_search is False:
            match = pattern.match(string)
        else:
            match = pattern.search(string)
        return bool(match)

    return _probe


def make_while_splitter_for_text_spans(
    start_condition: Probe[ProtectedTagOrStr],
    while_condition: Probe[ProtectedTagOrStr],
) -> Splitter[ProtectedTagOrStr, list[ProtectedTagOrStr]]:
    return make_while_splitter(
        pick_text_spans(start_condition),
        pick_if_transparent_tag_followed_by_match(pick_text_spans(while_condition)),
    )


def make_single_line_splitter_for_text_spans(
    is_matching: Probe[ProtectedTagOrStr],
) -> Splitter[ProtectedTagOrStr, list[ProtectedTagOrStr]]:
    return make_single_line_splitter(
        is_matching=pick_text_spans(is_matching),
    )


def make_pattern_splitter(
    pattern: PatternProxy,
) -> Splitter[ProtectedTagOrStr, MatchProxy]:
    def _splitter(
        elements: Sequence[ProtectedTagOrStr],
    ) -> RawSplit[ProtectedTagOrStr, MatchProxy] | None:
        splitted_elements = split_elements(elements, group_str_splitter)
        for i, grouped_strings in enumerate(splitted_elements):
            if not isinstance(grouped_strings, SplitMatch):
                continue

            string: str = merge_strings(map(get_string, grouped_strings.value))
            match_proxy = pattern.search(string)
            if not match_proxy:
                continue

            before = merge_splitted_elements(splitted_elements[:i])
            if match_proxy.start() > 0:
                before.append(string[: match_proxy.start()])

            after = merge_splitted_elements(splitted_elements[i + 1 :])
            if match_proxy.end() < len(string):
                after.insert(0, string[match_proxy.end() :])

            return (
                before,
                match_proxy,
                after,
            )
        return None

    return _splitter


group_text_span_tags_splitter = cast(
    Splitter[ProtectedTagOrStr, Sequence[ProtectedTagOrStr]],
    make_while_splitter(
        pick_text_spans(lambda elements, index: True),
        pick_if_transparent_tag_followed_by_match(pick_text_spans(lambda elements, index: True)),
    ),
)
"""
Splitter to enable grouping of text_span tags.
"""


group_str_splitter = cast(
    Splitter[ProtectedTagOrStr, Sequence[ProtectedTagOrStr]],
    make_while_splitter(
        pick_str(lambda elements, index: True),
        pick_str(lambda elements, index: True),
    ),
)
"""
Splitter to enable grouping of strings.
"""


def make_recombine_interrupted_lines_splitter(
    start_tag_spec: SemanticTagSpec,
) -> Splitter[ProtectedTagOrStr, Sequence[ProtectedTagOrStr]]:
    """
    Builds a splitter for groupping text that is interrupted by page separators.
    """

    def _splitter(
        elements: Sequence[ProtectedTagOrStr],
    ) -> RawSplit[ProtectedTagOrStr, list[ProtectedTagOrStr]] | None:
        before: list[ProtectedTagOrStr] = []
        while elements:
            # Find the next starting element
            before_start, elements = split_before_match(
                elements,
                lambda elements, i: is_semantic_tag(elements[i], spec_in=[start_tag_spec]),
            )
            before.extend(before_start)
            if not elements:
                break

            start_element = elements.pop(0)
            match_elements = [start_element]
            previous_text = get_string(start_element)
            # Continue to add elements as long as we find continuing sentences,
            # i.e a group that follows the pattern:
            #   <page_separator>    # One or several page separators
            #   <text_span>         # A text span that continues the previous text
            while True:
                page_separators, elements = split_before_match(
                    elements,
                    lambda elements, i: (
                        i > 0  # need at least one page separator
                        and all(
                            is_semantic_tag(element, spec_in=[PageSeparatorSpec])
                            for element in elements[:i]
                        )
                        and is_semantic_tag(elements[i], spec_in=[TextSpanSegmentationSpec])
                        and is_continuing_sentence(previous_text, get_string(elements[i]))
                    ),
                )

                if not elements:
                    # Restore elements if no match
                    elements = page_separators
                    break

                # We have a match, add the page separators and the next element.
                match_elements.extend(page_separators)
                next_element = elements.pop(0)
                match_elements.append(next_element)
                previous_text = get_string(next_element)

            if len(match_elements) > 1:
                return (before, match_elements, elements)
            else:
                before.extend(match_elements)

        return None

    return _splitter


def get_string(element: ProtectedTagOrStr) -> str:
    """
    Extracts the string from a Tag.
    If the element is a str, it returns it.
    If the element is a Tag, it recursively extracts strings from its text_span children.
    If its has other than text_span children, it will raises a ValueError.
    """
    if isinstance(element, str):
        return element
    elif is_semantic_tag(element):
        return merge_strings(map(_get_string, element.contents))
    else:
        raise ValueError(f"Element '{element}' is neither a string nor a Tag")


def _get_string(element: ProtectedTagOrStr) -> str:
    if isinstance(element, str):
        return element
    elif is_semantic_tag(element, spec_in=[TextSpanSegmentationSpec, *_STR_TAG_SPECS]):
        return merge_strings(map(_get_string, element.contents))
    elif is_semantic_tag(element, spec_in=TRANSPARENT_TAG_SPECS):
        return ""
    else:
        raise ValueError(f"Unexpected element '{element}'")


@iter_func_to_list
def get_strings(tags: Sequence[ProtectedTagOrStr]) -> Iterator[str]:
    for tag in tags:
        if is_semantic_tag(tag, spec_in=[TextSpanSegmentationSpec]):
            yield get_string(tag)
        elif is_semantic_tag(tag, spec_in=TRANSPARENT_TAG_SPECS):
            continue
        else:
            raise ValueError(f"Tag '{tag}' is not a text_span or a transparent tag")


def combine_text_spans(
    context: DocumentContext,
    elements: Sequence[ProtectedTagOrStr],
) -> ProtectedTag:
    """
    Combines a list of strings and text_span tags into a single text_span tag.
    """
    contents: list[ProtectedTagOrStr] = []
    first_text_span: ProtectedTag | None = None
    last_text_span: ProtectedTag | None = None
    for element in elements:
        if is_semantic_tag(element, spec_in=[TextSpanSegmentationSpec]):
            if first_text_span is None:
                first_text_span = element
            last_text_span = element
            for text_span_child in element.contents:
                if isinstance(text_span_child, str) or is_semantic_tag(
                    text_span_child, spec_in=TRANSPARENT_TAG_SPECS + _STR_TAG_SPECS
                ):
                    contents.append(text_span_child)
                else:
                    raise ValueError(f"Unexpected child '{text_span_child}' in of text_span tag")

        elif is_semantic_tag(element, spec_in=TRANSPARENT_TAG_SPECS):
            contents.append(element)

        else:
            raise ValueError(f"Unexpected element '{element}' ")

    assert first_text_span is not None and last_text_span is not None, "No text_span found"
    return make_semantic_tag(
        context.protected_soup,
        TextSpanSegmentationSpec,
        contents=contents,
        data=TextSpanSegmentationData(
            start=get_semantic_tag_data(TextSpanSegmentationSpec, first_text_span).start,
            end=get_semantic_tag_data(TextSpanSegmentationSpec, last_text_span).end,
        ),
    )
