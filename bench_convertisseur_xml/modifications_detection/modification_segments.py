import re
from typing import List, Pattern, Tuple, cast, Iterator
from dataclasses import dataclass

from bs4 import BeautifulSoup, Tag, PageElement

from bench_convertisseur_xml.utils.split import split_string_with_regex_at_beginning, merge_strings, split_string_with_regex_at_end
from bench_convertisseur_xml.utils.html import make_data_tag, make_new_tag, PageElementOrString
from bench_convertisseur_xml.utils.generators import remove_empty_strings_from_flow
from bench_convertisseur_xml.html_schemas import MODIFICATION_SEGMENT_SCHEMA
from bench_convertisseur_xml.types import ModificationType, PageElementOrString

SENTENCE_SPLIT_PATTERN = re.compile(r'\.')

DELETE_RE_LIST = [
    re.compile(r'abrog\w*', re.IGNORECASE),
    re.compile(r'suppr\w*', re.IGNORECASE),
]

ADD_RE_LIST = [
    re.compile(r'ins(e|é|è)r\w*', re.IGNORECASE),
    re.compile(r'ajout\w*', re.IGNORECASE),
    re.compile(r'complét\w*', re.IGNORECASE),
]

UPDATE_RE_LIST = [
    re.compile(r'modif\w*', re.IGNORECASE),
    re.compile(r'remplac\w*', re.IGNORECASE),
    re.compile(r'mise? [aà] jour', re.IGNORECASE),
]

PATTERNS_AND_TYPES = (
    [(pattern, ModificationType.DELETE) for pattern in DELETE_RE_LIST]
    + [(pattern, ModificationType.ADD) for pattern in ADD_RE_LIST]
    + [(pattern, ModificationType.UPDATE) for pattern in UPDATE_RE_LIST]
)


@dataclass(frozen=True)
class TargetGroup:
    previous: str | None
    target: Tag
    next: str | None


@remove_empty_strings_from_flow
def _tag_modification_segments(
    soup: BeautifulSoup, 
    children: List[PageElementOrString],
    modification_targets: List[Tag],
    patterns_and_types: List[Tuple[Pattern, ModificationType]],
) -> Iterator[PageElementOrString]:
    for element_or_group in _preprocess_children_by_adding_target_groups(soup, children, modification_targets):
        if not isinstance(element_or_group, TargetGroup):
            yield element_or_group
            continue
        
        if element_or_group.previous:
            for (pattern, modification_type) in patterns_and_types:
                match = pattern.search(element_or_group.previous)
                if match:
                    yield element_or_group.previous[:match.start()]
                    yield make_data_tag(
                        soup, 
                        MODIFICATION_SEGMENT_SCHEMA, 
                        contents=[
                            make_new_tag(soup, 'b', contents=[match.group(0)]),
                            element_or_group.previous[match.end():],
                        ], 
                        data=dict(
                            modification_type=modification_type.value,
                            keyword=match.group(0),
                        )
                    )
                    break
            # No match, we yield previous sibling with no modification
            else:
                yield element_or_group.previous

        yield element_or_group.target

        if element_or_group.next:
            for (pattern, modification_type) in patterns_and_types:
                match = pattern.search(element_or_group.next)
                if match:
                    yield make_data_tag(
                        soup, 
                        MODIFICATION_SEGMENT_SCHEMA, 
                        contents=[
                            element_or_group.next[:match.start()],
                            make_new_tag(soup, 'b', contents=[match.group(0)]),
                        ], 
                        data=dict(
                            modification_type=modification_type.value,
                            keyword=match.group(0),
                        )
                    )
                    yield element_or_group.next[match.end():]
                    break
            else:
                yield element_or_group.next


def _preprocess_children_by_adding_target_groups(
    soup: BeautifulSoup, 
    children: List[PageElementOrString],
    modification_targets: List[Tag],
) -> Iterator[PageElementOrString | TargetGroup]:
    next_children = children[:]

    while next_children:
        current_child = next_children.pop(0)
        previous_sibling: PageElementOrString | None = None

        if next_children and next_children[0] in modification_targets:
            previous_sibling = current_child
            current_child = next_children.pop(0)

        if current_child in modification_targets:
            previous_sibling_remainder: str | None = None
            previous_sibling_str: str | None = None
            if isinstance(previous_sibling, str):
                split_match = split_string_with_regex_at_end(SENTENCE_SPLIT_PATTERN, previous_sibling)
                if split_match:
                    previous_sibling_remainder, match, previous_sibling_str = split_match
                    previous_sibling_remainder += match.group(0)
                else:
                    previous_sibling_str = previous_sibling

            next_sibling_remainder: str | None = None
            next_sibling_str: str | None = None
            next_sibling: PageElementOrString | None = None
            if next_children:
                next_sibling = next_children.pop(0)
            if isinstance(next_sibling, str):
                split_match = split_string_with_regex_at_beginning(SENTENCE_SPLIT_PATTERN, next_sibling)
                if split_match:
                    next_sibling_str, match, next_sibling_remainder = split_match
                    next_sibling_remainder = match.group(0) + next_sibling_remainder 
                else:
                    next_sibling_str = next_sibling

            if isinstance(previous_sibling, Tag):
                yield previous_sibling
            elif previous_sibling_remainder:
                yield previous_sibling_remainder
            
            yield TargetGroup(
                previous=previous_sibling_str, 
                target=cast(Tag, current_child), 
                next=next_sibling_str,
            )
            
            if isinstance(next_sibling, Tag):
                yield next_sibling
            elif next_sibling_remainder:
                next_children = cast(List[PageElementOrString], [next_sibling_remainder]) + next_children

        else:
            yield current_child


def tag_modification_segments(
    soup: BeautifulSoup, 
    children: List[PageElementOrString],
    modification_targets: List[Tag],
) -> List[PageElementOrString]:
    return list(
        merge_strings(
            _tag_modification_segments(soup, children, modification_targets, PATTERNS_AND_TYPES)
        )
    )