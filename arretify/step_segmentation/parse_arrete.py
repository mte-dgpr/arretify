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
from arretify.types import DocumentContext
from arretify.html_schemas import (
    HEADER_SCHEMA,
    MAIN_SCHEMA,
    APPENDIX_SCHEMA,
)
from arretify.utils.html import make_data_tag
from .header import parse_header
from .content import parse_content


def parse_arrete(document_context: DocumentContext) -> DocumentContext:
    body = document_context.soup.body
    assert body

    lines = document_context.lines

    if lines:
        header = make_data_tag(document_context.soup, HEADER_SCHEMA)
        body.append(header)
        lines = parse_header(document_context.soup, header, lines)

    if lines:
        main_content = make_data_tag(document_context.soup, MAIN_SCHEMA)
        body.append(main_content)
        lines = parse_content(document_context.soup, main_content, lines, exit_on_appendix=True)

    if lines:
        appendix = make_data_tag(document_context.soup, APPENDIX_SCHEMA)
        body.append(appendix)
        lines = parse_content(document_context.soup, appendix, lines, exit_on_appendix=False)

    return document_context
