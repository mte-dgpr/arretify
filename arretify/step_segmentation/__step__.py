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
from typing import List, cast


from arretify.types import DocumentContext
from .parse_arrete import parse_arrete, render_arrete
from .core import NodeOrText


def step_segmentation(document_context: DocumentContext) -> DocumentContext:
    if not document_context.lines:
        raise ValueError("Parsing context does not contain any lines to segment")

    body = document_context.soup.body
    assert body

    lines = document_context.lines
    assert lines

    body.extend(
        render_arrete(
            document_context.soup,
            parse_arrete(cast(List[NodeOrText], lines)),
        )
    )

    return document_context
