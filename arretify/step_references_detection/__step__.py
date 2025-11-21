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

from typing import Sequence

from arretify.semantic_tag_specs import AlineaSpec, MotifSpec, VisaSpec
from arretify.types import DocumentContext, ProtectedTagOrStr
from arretify.utils.html_create import replace_contents
from arretify.utils.html_semantic import css_selector
from arretify.utils.html_split_merge import recombine_strings
from arretify.utils.references import iter_reference_trees

from .arretes_detection import parse_arretes_references
from .circulaires_detection import parse_circulaires_references
from .codes_detection import parse_codes_references
from .decrets_detection import parse_decrets_references
from .eu_acts_detection import parse_eu_acts_references
from .match_sections_with_documents import match_sections_to_parents
from .sections_detection import parse_section_references
from .self_detection import parse_self_references
from .unknown_sections_resolution import remove_misdetected_sections, resolve_unknown_sections

REFERENCES_CONTAINER_SELECTOR = (
    f"{css_selector(AlineaSpec)}, {css_selector(AlineaSpec)} *"
    + f", {css_selector(MotifSpec)}, {css_selector(VisaSpec)}"
)


def step_references_detection(document_context: DocumentContext) -> DocumentContext:
    contents: Sequence[ProtectedTagOrStr]

    # Parse documents and sections references
    for tag in document_context.protected_soup.select(REFERENCES_CONTAINER_SELECTOR):
        contents = list(tag.contents)
        contents = parse_arretes_references(document_context, contents)
        contents = parse_decrets_references(document_context, contents)
        contents = parse_circulaires_references(document_context, contents)
        contents = parse_codes_references(document_context, contents)
        contents = parse_self_references(document_context, contents)
        contents = parse_eu_acts_references(document_context, contents)
        contents = parse_section_references(document_context, contents)
        replace_contents(tag, contents)

    # Match sections with documents
    for tag in document_context.protected_soup.select(REFERENCES_CONTAINER_SELECTOR):
        contents = list(tag.contents)
        contents = match_sections_to_parents(document_context, contents)
        replace_contents(tag, contents)

    for reference_tree in iter_reference_trees(document_context.protected_soup):
        resolve_unknown_sections(
            document_context,
            reference_tree,
        )

    # Cleaning steps
    for tag in document_context.protected_soup.select(REFERENCES_CONTAINER_SELECTOR):
        contents = list(tag.contents)
        contents = list(remove_misdetected_sections(document_context, contents))
        contents = recombine_strings(contents)
        replace_contents(tag, contents)

    return document_context
