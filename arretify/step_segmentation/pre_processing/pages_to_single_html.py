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
from typing import Iterator, Sequence

from arretify.semantic_tag_specs import (
    PageFooterSpec,
    PageHeaderSpec,
    PageSeparatorData,
    PageSeparatorSpec,
)
from arretify.step_segmentation.semantic_tag_specs import (
    TextSpanSegmentationData,
    TextSpanSegmentationSpec,
)
from arretify.types import DocumentContext, ProtectedTagOrStr
from arretify.utils.functional import iter_func_to_list
from arretify.utils.html_create import make_semantic_tag, wrap_in_tag
from arretify.utils.ocr_document import Page, get_or_load_asset
from arretify.utils.strings import split_on_newlines


@iter_func_to_list
def pages_to_single_html(
    document_context: DocumentContext,
    pages: Sequence[Page]
) -> Iterator[ProtectedTagOrStr]:
    for page in pages:
        yield make_semantic_tag(
            document_context.protected_soup,
            PageSeparatorSpec,
            contents=[],
            # Separator situates before the page content, so page index is page.index - 1
            data=PageSeparatorData(page_index=page.index - 1),
        )

        if "header.md" in page.assets:
            header_content = get_or_load_asset(page, "header.md")
            yield make_semantic_tag(
                document_context.protected_soup,
                PageHeaderSpec,
                contents=wrap_in_tag(
                    document_context.protected_soup,
                    "div",
                    [header_content],
                ),
            )

        page_lines = split_on_newlines(get_or_load_asset(page, "main.md"))
        for line_index, line in enumerate(page_lines):
            yield make_semantic_tag(
                document_context.protected_soup,
                TextSpanSegmentationSpec,
                contents=[line],
                data=TextSpanSegmentationData(
                    start=[page.index, line_index, 0],
                    end=[page.index, line_index, len(line) - 1],
                ),
            )

        if "footer.md" in page.assets:
            footer_content = get_or_load_asset(page, "footer.md")
            yield make_semantic_tag(
                document_context.protected_soup,
                PageFooterSpec,
                contents=wrap_in_tag(
                    document_context.protected_soup,
                    "div",
                    [footer_content],
                ),
            )
