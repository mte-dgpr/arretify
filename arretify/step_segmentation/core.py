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
from typing import (
    Sequence,
    cast,
    Iterator,
)

from bs4 import Tag

from arretify.parsing_utils.patterns import is_continuing_sentence
from arretify.semantic_tag_specs import PageFooterSpec, PageSeparatorSpec
from arretify.step_segmentation.semantic_tag_specs import AddressSpec, TextSpanData, TextSpanSpec
from arretify.types import DocumentContext, PageElementOrString
from arretify.utils.functional import iter_func_to_list
from arretify.regex_utils import PatternProxy, MatchProxy
from arretify.utils.html_semantic import (
    SemanticTagSpec,
    get_semantic_tag_data,
    is_semantic_tag,
    make_semantic_tag,
)
from arretify.utils.strings import merge_strings
from arretify.utils.split_merge import (
    make_while_splitter,
    make_single_line_splitter,
    Splitter,
    Probe,
    RawSplit,
    split_elements,
    merge_splitted_elements,
    SplitMatch,
    split_before_match,
)


TRANSPARENT_TAG_SPECS = [PageSeparatorSpec, PageFooterSpec]
"""
List of tag names that are considered transparent for text extraction purposes.
"""

INLINE_TAG_SPECS = [AddressSpec]
"""
List of tag names that contains specific bits of text information inside a text_span.
"""


def pick_if_transparent_tag_followed_by_match(
    is_matching: Probe[PageElementOrString],
) -> Probe[PageElementOrString]:
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
    >>> def is_string(elements: Sequence[PageElementOrString], index: int) -> bool:
    ...     return isinstance(elements[index], str)
    >>> probe = pick_if_transparent_tag_followed_by_match(is_string)
    >>> probe(elements, 0) # -> directly calls `is_string`
    True
    >>> probe(elements, 1) # -> calls `is_string` on the next element
    True
    >>> probe(elements, 3) # -> calls `is_string` on the next element
    False
    """

    def _probe(elements: Sequence[PageElementOrString], index: int) -> bool:
        for next_index, next_element in enumerate(elements[index:], start=index):
            if is_semantic_tag(next_element, spec_in=TRANSPARENT_TAG_SPECS):
                continue
            else:
                return is_matching(elements, next_index)
        return False

    return _probe


def pick_text_spans(
    probe: Probe[PageElementOrString],
) -> Probe[PageElementOrString]:
    def _probe(elements: Sequence[PageElementOrString], index: int) -> bool:
        element = elements[index]
        if is_semantic_tag(element, spec_in=[TextSpanSpec]):
            return probe(elements, index)
        return False

    return _probe


def pick_str(
    probe: Probe[PageElementOrString],
) -> Probe[PageElementOrString]:
    def _probe(elements: Sequence[PageElementOrString], index: int) -> bool:
        element = elements[index]
        if isinstance(element, str):
            return probe(elements, index)
        return False

    return _probe


def make_probe_from_pattern_proxy(
    pattern: PatternProxy, use_search: bool = False
) -> Probe[PageElementOrString]:
    def _probe(elements: Sequence[PageElementOrString], index: int) -> bool:
        string = get_string(elements[index])
        if use_search is False:
            match = pattern.match(string)
        else:
            match = pattern.search(string)
        return bool(match)

    return _probe


def make_while_splitter_for_text_spans(
    start_condition: Probe[PageElementOrString],
    while_condition: Probe[PageElementOrString],
) -> Splitter[PageElementOrString, list[PageElementOrString]]:
    return make_while_splitter(
        pick_text_spans(start_condition),
        pick_if_transparent_tag_followed_by_match(pick_text_spans(while_condition)),
    )


def make_single_line_splitter_for_text_spans(
    is_matching: Probe[PageElementOrString],
) -> Splitter[PageElementOrString, list[PageElementOrString]]:
    return make_single_line_splitter(
        is_matching=pick_text_spans(is_matching),
    )


def make_pattern_splitter(
    pattern: PatternProxy,
) -> Splitter[PageElementOrString, MatchProxy]:
    def _splitter(
        elements: Sequence[PageElementOrString],
    ) -> RawSplit[PageElementOrString, MatchProxy] | None:
        splitted_elements = split_elements(elements, group_str_splitter)
        for i, splitted_element in enumerate(splitted_elements):
            if not isinstance(splitted_element, SplitMatch):
                continue

            string: str = merge_strings([get_string(element) for element in splitted_element.value])
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
    Splitter[PageElementOrString, Sequence[PageElementOrString]],
    make_while_splitter(
        pick_text_spans(lambda elements, index: True),
        pick_if_transparent_tag_followed_by_match(pick_text_spans(lambda elements, index: True)),
    ),
)
"""
Splitter to enable grouping of text_span tags.
"""


group_str_splitter = cast(
    Splitter[PageElementOrString, Sequence[PageElementOrString]],
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
) -> Splitter[PageElementOrString, Sequence[PageElementOrString]]:
    """
    Builds a splitter for groupping text that is interrupted by page separators.
    """

    def _splitter(
        elements: Sequence[PageElementOrString],
    ) -> RawSplit[PageElementOrString, list[PageElementOrString]] | None:
        before: list[PageElementOrString] = []
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
                        and is_semantic_tag(elements[i], spec_in=[TextSpanSpec])
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


def get_string(element: PageElementOrString) -> str:
    """
    Extracts the string from a Tag.
    If the element is a str, it returns it.
    If the element is a Tag, it recursively extracts strings from its text_span children.
    If its has other than text_span children, it will raises a ValueError.
    """
    if isinstance(element, str):
        return element
    elif is_semantic_tag(element):
        strings: list[str] = [_get_string(child) for child in element.contents]
        return merge_strings(strings)
    else:
        raise ValueError(f"Element '{element}' is neither a string nor a Tag")


def _get_string(element: PageElementOrString) -> str:
    if isinstance(element, str):
        return element
    elif is_semantic_tag(element, spec_in=[TextSpanSpec, *INLINE_TAG_SPECS]):
        return merge_strings(_get_string(child) for child in element.contents)
    elif is_semantic_tag(element, spec_in=TRANSPARENT_TAG_SPECS):
        return ""
    else:
        raise ValueError(f"Unexpected element '{element}'")


@iter_func_to_list
def get_strings(tags: Sequence[PageElementOrString]) -> Iterator[str]:
    for tag in tags:
        if is_semantic_tag(tag, spec_in=[TextSpanSpec]):
            yield get_string(tag)
        elif is_semantic_tag(tag, spec_in=TRANSPARENT_TAG_SPECS):
            continue
        else:
            raise ValueError(f"Tag '{tag}' is not a text_span or a transparent tag")


def combine_text_spans(
    context: DocumentContext,
    elements: Sequence[PageElementOrString],
) -> Tag:
    """
    Combines a list of strings and text_span tags into a single text_span tag.
    """
    children: list[PageElementOrString] = []
    first_text_span: Tag | None = None
    last_text_span: Tag | None = None
    for element in elements:
        if is_semantic_tag(element, spec_in=[TextSpanSpec]):
            if first_text_span is None:
                first_text_span = element
            last_text_span = element
            for text_span_child in element.children:
                if isinstance(text_span_child, str) or is_semantic_tag(
                    text_span_child, spec_in=TRANSPARENT_TAG_SPECS + INLINE_TAG_SPECS
                ):
                    children.append(text_span_child)
                else:
                    raise ValueError(f"Unexpected child '{text_span_child}' in of text_span tag")

        elif is_semantic_tag(element, spec_in=TRANSPARENT_TAG_SPECS):
            children.append(element)

        else:
            raise ValueError(f"Unexpected element '{element}' ")

    assert first_text_span is not None and last_text_span is not None, "No text_span found"
    return make_semantic_tag(
        context.soup,
        TextSpanSpec,
        contents=children,
        data=TextSpanData(
            start=get_semantic_tag_data(TextSpanSpec, first_text_span).start,
            end=get_semantic_tag_data(TextSpanSpec, last_text_span).end,
        ),
    )
