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
from typing import List


from arretify.types import PageElementOrString, DocumentContext
from arretify.utils.html import make_css_class, replace_children
from arretify.html_schemas import (
    ALINEA_SCHEMA,
    MOTIF_SCHEMA,
    VISA_SCHEMA,
)

from .sections_detection import (
    parse_section_references,
)
from .arretes_detection import (
    parse_arretes_references,
)
from .decrets_detection import (
    parse_decrets_references,
)
from .circulaires_detection import (
    parse_circulaires_references,
)
from .codes_detection import (
    parse_codes_references,
)
from .self_detection import parse_self_references
from .eu_acts_detection import (
    parse_eu_acts_references,
)
from .match_sections_with_documents import match_sections_to_parents


ALINEA_CSS_CLASS = make_css_class(ALINEA_SCHEMA)
MOTIF_CSS_CLASS = make_css_class(MOTIF_SCHEMA)
VISA_CSS_CLASS = make_css_class(VISA_SCHEMA)


def step_references_detection(document_context: DocumentContext) -> DocumentContext:
    new_children: List[PageElementOrString]

    # Parse documents and sections references
    for tag in document_context.soup.select(
        f".{ALINEA_CSS_CLASS}, .{ALINEA_CSS_CLASS} *, .{MOTIF_CSS_CLASS}, .{VISA_CSS_CLASS}"
    ):
        new_children = list(tag.children)
        new_children = parse_arretes_references(document_context, new_children)
        new_children = parse_decrets_references(document_context, new_children)
        new_children = parse_circulaires_references(document_context, new_children)
        new_children = parse_codes_references(document_context, new_children)
        new_children = parse_self_references(document_context, new_children)
        new_children = parse_eu_acts_references(document_context, new_children)
        new_children = parse_section_references(document_context, new_children)
        replace_children(tag, new_children)

    # Match sections with documents
    for tag in document_context.soup.select(
        f".{ALINEA_CSS_CLASS}, .{ALINEA_CSS_CLASS} *, .{MOTIF_CSS_CLASS}, .{VISA_CSS_CLASS}"
    ):
        new_children = list(tag.children)
        new_children = match_sections_to_parents(document_context, new_children)
        replace_children(tag, new_children)

    return document_context
