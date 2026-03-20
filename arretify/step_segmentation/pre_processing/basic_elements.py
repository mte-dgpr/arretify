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
import logging
from typing import Iterator, Sequence, cast
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from arretify.regex_utils.core import PatternProxy
from arretify.semantic_tag_specs import (
    PageFooterSpec,
    PageHeaderSpec,
    PageSeparatorData,
    PageSeparatorSpec,
)
from arretify.step_segmentation.core import make_probe_from_pattern_proxy
from arretify.step_segmentation.semantic_tag_specs import (
    TextSpanSegmentationData,
    TextSpanSegmentationSpec,
)
from arretify.step_segmentation.titles_detection import TITLE_NODE
from arretify.types import DocumentContext, ProtectedTag, ProtectedTagOrStr
from arretify.utils.functional import iter_func_to_list
from arretify.utils.html import is_tag, set_attribute
from arretify.utils.html_create import make_semantic_tag, wrap_in_tag
from arretify.utils.markdown_parsing import IMAGE_PATTERN_S, LINK_PATTERN_S, parse_markdown_element
from arretify.utils.ocr_document import Page, get_or_load_asset_content
from arretify.utils.strings import split_on_newlines

_LOGGER = logging.getLogger(__name__)


@iter_func_to_list
def parse_basic_elements(context: DocumentContext, page: Page) -> Iterator[ProtectedTagOrStr]:
    yield render_page_separator(context, page)

    if "header.md" in page.assets:
        header_content = get_or_load_asset_content(page.assets["header.md"])
        header_lines = split_on_newlines(header_content)
        if _is_containing_title(header_lines):
            # If the header contains a title we consider that it is misdetected
            # and we promote it to main content.
            for line in header_lines:
                yield render_text_segmentation_tag(context, page, 0, line)
        else:
            yield render_page_header(context, header_content)

    page_lines = split_on_newlines(get_or_load_asset_content(page.assets["main.md"]))
    for line_index, line in enumerate(page_lines):
        if _is_image(page_lines, line_index):
            yield render_image_and_embed_base64(page, line)

        elif _is_link(page_lines, line_index):
            loaded_tag = load_tag_from_markdown_link(page, line)
            if loaded_tag is not None and is_tag(loaded_tag, tag_name_in=["table"]):
                if _is_frame_misdetected_as_table(loaded_tag):
                    yield from render_frame_misdetected_as_table(
                        context, page, line_index, loaded_tag
                    )
                else:
                    yield loaded_tag
            else:
                yield render_text_segmentation_tag(context, page, line_index, line)

        else:
            yield render_text_segmentation_tag(context, page, line_index, line)

    if "footer.md" in page.assets:
        yield render_page_footer(context, get_or_load_asset_content(page.assets["footer.md"]))


# -------------------- Page header, footer and separator -------------------- #
_is_title_string = make_probe_from_pattern_proxy(
    TITLE_NODE.pattern,
)


def _is_containing_title(lines: Sequence[str]) -> bool:
    return any(_is_title_string(lines, i) for i in range(len(lines)))


def render_page_header(context: DocumentContext, content: str) -> ProtectedTag:
    """
    Mistral OCR 3 often detects the title of the document as a page header.
    When that happens, we promote the header to main content.
    """
    return make_semantic_tag(
        context.protected_soup,
        PageHeaderSpec,
        contents=wrap_in_tag(
            context.protected_soup,
            "div",
            [content],
        ),
    )


def render_page_footer(context: DocumentContext, content: str) -> ProtectedTag:
    return make_semantic_tag(
        context.protected_soup,
        PageFooterSpec,
        contents=wrap_in_tag(
            context.protected_soup,
            "div",
            [content],
        ),
    )


def render_page_separator(context: DocumentContext, page: Page) -> ProtectedTag:
    return make_semantic_tag(
        context.protected_soup,
        PageSeparatorSpec,
        contents=[],
        # Separator situates before the page content, so page index is page.index - 1
        data=PageSeparatorData(page_index=page.index - 1),
    )


# -------------------- Images -------------------- #
_is_image = make_probe_from_pattern_proxy(PatternProxy(r"^" + IMAGE_PATTERN_S + "$"))


def render_image_and_embed_base64(page: Page, markdown_image: str) -> ProtectedTag:
    img_tag = parse_markdown_element(markdown_image, "img")

    img_url = img_tag.get("src", "")
    assert isinstance(img_url, str)

    # Ignore base64 urls, they are already embedded.
    # Ignore also external urls, as we only want to embed local images.
    parsed_url = urlparse(img_url)
    if not img_url or parsed_url.scheme in ("http", "https", "data"):
        return img_tag

    img_filename = parsed_url.path.split("/")[-1]
    img_contents = get_or_load_asset_content(page.assets[img_filename])
    # If the content is not a base64 string, we cannot embed it.
    if not img_contents.startswith("data:image/"):
        return img_tag

    return set_attribute(img_tag, "src", img_contents)


# -------------------- Text segmentation tag -------------------- #
def render_text_segmentation_tag(
    context: DocumentContext, page: Page, line_index: int, line: str
) -> ProtectedTag:
    return make_semantic_tag(
        context.protected_soup,
        TextSpanSegmentationSpec,
        contents=[line],
        data=TextSpanSegmentationData(
            start=[page.index, line_index, 0],
            end=[page.index, line_index, len(line) - 1],
        ),
    )


# -------------------- Embedded HTML content -------------------- #
_is_link = make_probe_from_pattern_proxy(PatternProxy(r"^" + LINK_PATTERN_S + "$"))


def _is_frame_misdetected_as_table(tag: ProtectedTag) -> bool:
    """
    Mistral OCR 3 sometimes falsly detects tables that are actually just frames,
    i.e. tables with only one cell, used to create a border around some content.
    """
    if not is_tag(tag, tag_name_in=["table"]):
        return False
    return len(tag.select("tr")) == 1 and len(tag.select("td")) == 1


def load_tag_from_markdown_link(
    page: Page,
    markdown_link: str,
) -> ProtectedTagOrStr | None:
    """
    Mistral OCR 3 detects tables and extracts them as separate HTML files,
    linked in the main markdown file. For example `[tbl-0.html](tbl-0.html)`.

    This function parses the markdown link, and loads the linked HTML table
    from the corresponding asset.
    """
    a_tag = parse_markdown_element(markdown_link, "a")

    a_href = a_tag.get("href", "")
    if not a_href:
        return None

    # Ignore external urls, as we only want to embed local content.
    # Select only .html files.
    parsed_url = urlparse(a_href)
    if parsed_url.scheme in ("http", "https") or not a_href.endswith(".html"):
        return None

    html_filename = parsed_url.path.split("/")[-1]
    html_contents = get_or_load_asset_content(page.assets[html_filename])
    parsed_html = BeautifulSoup(html_contents, features="html.parser")

    # If the parsed HTML doesn't contain exactly one element,
    # we cannot be sure of what to embed, so we return the original link.
    if len(parsed_html.contents) != 1:
        _LOGGER.warning(
            f"Linked HTML file '{html_filename}' does not contain exactly one root element. "
            "Cannot embed content, returning original link."
        )
        return None

    element = cast(ProtectedTagOrStr, parsed_html.contents[0])
    return element


def render_frame_misdetected_as_table(
    context: DocumentContext, page: Page, line_index: int, frame_tag: ProtectedTag
) -> Iterator[ProtectedTag]:
    """
    Extracts the text content of the frame and renders it as separate text segmentation tags.
    """
    results = frame_tag.select("td")
    assert len(results) == 1
    td = results[0]
    for element in td.contents:
        if is_tag(element, tag_name_in=["br"]):
            continue
        elif isinstance(element, str):
            yield render_text_segmentation_tag(context, page, line_index, element)
        else:
            raise ValueError(f"Unexpected in frame: {element}")
