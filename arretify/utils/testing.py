import re
from typing import Callable, List, Iterable, TypeVar

from bs4 import Tag, BeautifulSoup, PageElement, NavigableString

from arretify.types import PageElementOrString
from arretify.utils.html import replace_children


_INLINE_TAGS = [
    "a",
    "abbr",
    "acronym",
    "b",
    "bdo",
    "big",
    "cite",
    "code",
    "em",
    "i",
    "kbd",
    "mark",
    "q",
    "samp",
    "small",
    "span",
    "strong",
    "sub",
    "sup",
    "time",
    "u",
    "var",
    "wbr",
    "br",
    "img",
    "hr",
    "input",
    "select",
    "textarea",
    "button",
    "label",
]
_INDENTATION_PATTERN = re.compile(r"\n[\s\t]{2,}")
_NO_CONTENT = re.compile(r"^[\s]*$")

P = TypeVar("P", bound=Tag | BeautifulSoup)


def make_testing_function_for_single_tag(
    process_function: Callable[[Tag], None],
) -> Callable[[str], str]:
    def _testing_function(string: str, css_selector: str | None = None) -> str:
        soup = create_bs(normalized_html_str(string))

        tag_list: List[PageElement]
        if css_selector is None:
            tag_list = list(soup.children)
        else:
            tag_list = list(soup.select(css_selector))
        tag_list = [tag for tag in tag_list if isinstance(tag, Tag)]

        if len(tag_list) != 1:
            raise ValueError("One and only one tag must be found")

        if not isinstance(tag_list[0], Tag):
            raise ValueError("No tag found")

        tag = tag_list[0]
        process_function(tag)
        return normalized_html_str(str(tag))

    return _testing_function


def make_testing_function_for_children_list(
    process_function: Callable[
        [BeautifulSoup, Iterable[PageElementOrString]],
        List[PageElementOrString],
    ],
) -> Callable[[str], str]:
    def _testing_function(string: str):
        soup = create_bs(normalized_html_str(string))
        elements = process_function(soup, soup.children)
        return [
            normalized_html_str(str(element)) if isinstance(element, Tag) else str(element)
            for element in elements
        ]

    return _testing_function


def create_bs(html: str) -> BeautifulSoup:
    return BeautifulSoup(
        html,
        features="html.parser",
    )


def normalized_html_str(html: str) -> str:
    """
    Normalize the HTML string by removing unnecessary whitespace and
    indentation, and ensuring consistent formatting.
    Allows to write tests with a multiline HTML strings. For example :

        <div>
            <span>bli</span>
            bla
            blo
        </div>

    becomes :

        <div><span>bli</span> bla blo</div>
    """
    return str(
        _normalize_tag(
            BeautifulSoup(
                html,
                features="html.parser",
            )
        )
    )


def _normalize_string(nav_string: NavigableString) -> str | None:
    strip_chars = " \n\t"
    string = str(nav_string)
    string = _INDENTATION_PATTERN.sub(" ", string)

    if _NO_CONTENT.match(string):
        return None

    def _ensure_space_right(string: str) -> str:
        if string and string[-1] != " ":
            return string + " "
        return string

    def _ensure_space_left(string: str) -> str:
        if string and string[0] != " ":
            return " " + string
        return string

    if nav_string.previous_sibling is None:
        string = string.lstrip(strip_chars)
    elif isinstance(nav_string.previous_sibling, Tag):
        if nav_string.previous_sibling.name in _INLINE_TAGS:
            string = _ensure_space_left(string)
        else:
            string = string.lstrip(strip_chars)

    if nav_string.next_sibling is None:
        string = string.rstrip(strip_chars)
    elif isinstance(nav_string.next_sibling, Tag):
        if nav_string.next_sibling.name in _INLINE_TAGS:
            string = _ensure_space_right(string)
        else:
            string = string.rstrip(strip_chars)
    elif isinstance(nav_string.next_sibling, str):
        string = _ensure_space_right(string)

    return string


def _normalize_tag(tag: P) -> P:
    new_children: List[PageElementOrString] = []
    for child in tag.children:
        if isinstance(child, NavigableString):
            normalized_string = _normalize_string(child)
            if normalized_string is not None:
                new_children.append(normalized_string)
        elif isinstance(child, (Tag, BeautifulSoup)):
            new_children.append(_normalize_tag(child))
    replace_children(tag, new_children)
    return tag
