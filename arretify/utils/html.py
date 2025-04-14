from typing import Dict, List, Iterable, cast

from bs4 import BeautifulSoup, Tag

from arretify.utils.merge import merge_strings
from arretify.types import (
    DataElementSchema,
    PageElementOrString,
    ElementId,
)


_ID_COUNTER = 0


def make_css_class(schema: DataElementSchema):
    return f"dsr-{schema.name}"


def has_css_class(tag: Tag, css_class: str) -> bool:
    return css_class in tag.get("class", [])


def assign_element_id(tag: Tag) -> ElementId:
    global _ID_COUNTER
    if "data-element_id" in tag.attrs:
        return cast(ElementId, tag["data-element_id"])
    _ID_COUNTER += 1
    element_id: ElementId = f"{_ID_COUNTER}"
    tag["data-element_id"] = element_id
    return element_id


def make_data_tag(
    soup: BeautifulSoup,
    schema: DataElementSchema,
    contents: Iterable[PageElementOrString] | None = None,
    data: Dict[str, str | None] | None = None,
) -> Tag:
    if contents is None:
        contents = []
    if data is None:
        data = {}
    element = make_new_tag(soup, schema.tag_name, contents=contents)
    element["class"] = [make_css_class(schema)]
    for key in schema.data_keys:
        try:
            data_value = data[key]
        except KeyError:
            raise KeyError(f'Missing key "{key}" for schema "{schema.name}"')
        if data_value is not None:
            element[f"data-{key}"] = data_value
    return element


def wrap_in_tag(
    soup: BeautifulSoup,
    elements: List[PageElementOrString],
    tag_name: str,
) -> List[Tag]:
    wrapped: List[Tag] = []
    for element in elements:
        if isinstance(element, str) and element.strip():
            container = soup.new_tag(tag_name)
            wrapped.append(container)
            container.append(element)
    return wrapped


def make_ul(soup: BeautifulSoup, elements: List[PageElementOrString]):
    ul = soup.new_tag("ul")
    for element in elements:
        if isinstance(element, Tag) and element.name == "li":
            li = element
        else:
            li = make_li(soup, [element])
        ul.append(li)
    return ul


def make_li(soup: BeautifulSoup, elements: List[PageElementOrString]):
    li = soup.new_tag("li")
    li.extend(elements)
    return li


def make_new_tag(
    soup: BeautifulSoup,
    tag_name: str,
    contents: Iterable[PageElementOrString] | None = None,
) -> Tag:
    if contents is None:
        contents = []
    element = soup.new_tag(tag_name)
    element.extend(merge_strings(contents))
    return element


def parse_bool_attribute(value: str) -> bool:
    return value == "true"


def render_bool_attribute(value: bool) -> str:
    return "true" if value else "false"


def parse_str_list_attribute(value: str) -> List[str]:
    return value.split(",")


def render_str_list_attribute(value: List[str]) -> str:
    for item in value:
        if "," in item:
            raise ValueError(f'Invalid item "{item}" in list')
    return ",".join(value)


def replace_children(
    tag: Tag,
    new_children: Iterable[PageElementOrString],
) -> None:
    tag.clear()
    tag.extend(new_children)
