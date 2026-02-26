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
import importlib.metadata

from arretify.semantic_tag_specs import ArreteData, ArreteSpec
from arretify.types import DocumentContext
from arretify.utils.html_create import replace_contents, upgrade_to_semantic_tag

from .parse_arrete import parse_arrete
from .pre_processing import step_segmentation_pre_processing
from .render_contents import render_contents

ARRETIFY_VERSION = importlib.metadata.version("arretify")


def step_segmentation(document_context: DocumentContext) -> DocumentContext:
    ocr_document = document_context.ocr_document
    if not ocr_document:
        raise ValueError("Parsing context does not contain any ocr document to segment")

    body = document_context.protected_soup.body
    assert body
    upgrade_to_semantic_tag(
        body,
        ArreteSpec,
        ArreteData(
            input_name=document_context.input_path.name if document_context.input_path else None,
            arretify_version=ARRETIFY_VERSION,
        ),
    )

    # Render segmented arrete contents and set it to body.
    replace_contents(
        body,
        render_contents(
            document_context,
            parse_arrete(document_context, step_segmentation_pre_processing(document_context, ocr_document)),
        ),
    )

    return document_context
