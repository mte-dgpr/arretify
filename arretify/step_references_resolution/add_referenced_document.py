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

# TODO : this is a temporary solution, but eventually we need to
# refactor the URI system which is not really adapted to the new
# way of referencing documents from sections.

from typing import cast

from arretify.types import DocumentContext
from arretify.utils.html import make_css_class, is_tag_and_matches
from arretify.html_schemas import SECTION_REFERENCE_SCHEMA, DOCUMENT_REFERENCE_SCHEMA
from arretify.law_data.uri import parse_uri, render_uri
from arretify.law_data.types import Document, Section
from arretify.step_references_detection.match_sections_with_documents import build_reference_tree


SECTION_REFERENCE_CSS_CLASS = make_css_class(SECTION_REFERENCE_SCHEMA)
DOCUMENT_REFERENCE_CSS_CLASS = make_css_class(DOCUMENT_REFERENCE_SCHEMA)


def add_referenced_document_DEPRECATED(
    document_context: DocumentContext,
) -> None:
    """
    This function is deprecated and will be removed in a future version.
    It is a temporary solution to duplicate the document part of the uri
    into the section reference tag.
    Eventually section reference will only use element_id to link the document reference.
    """

    for section_reference_tag in document_context.soup.select(f".{SECTION_REFERENCE_CSS_CLASS}"):
        reference_branches = build_reference_tree(section_reference_tag)
        for branch in reference_branches:
            document: Document | None = None
            sections: list[Section] = []
            for reference_tag in branch:
                if is_tag_and_matches(reference_tag, css_classes_in=[DOCUMENT_REFERENCE_CSS_CLASS]):
                    if document is not None:
                        raise ValueError("Multiple document references found in the same branch")
                    _document, _ = parse_uri(cast(str, reference_tag["data-uri"]))
                    document = _document

                elif is_tag_and_matches(
                    reference_tag, css_classes_in=[SECTION_REFERENCE_CSS_CLASS]
                ):
                    _, _sections = parse_uri(cast(str, reference_tag["data-uri"]))
                    sections.append(_sections[-1])

                    if document is not None:
                        reference_tag["data-uri"] = render_uri(document, *sections)
