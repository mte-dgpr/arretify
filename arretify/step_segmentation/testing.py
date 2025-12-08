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
from functools import partial

from arretify.step_segmentation.semantic_tag_specs import TextSpanSegmentationSpec
from arretify.types import ProtectedTag
from arretify.utils.html_create import make_semantic_tag
from arretify.utils.testing import DEFAULT_TEXT_SPAN_DATA, BaseTestCaseHtml


def _make_text_spans(soup, *lines: str) -> list[ProtectedTag]:
    return [
        make_semantic_tag(
            soup,
            TextSpanSegmentationSpec,
            contents=[line],
            data=DEFAULT_TEXT_SPAN_DATA,
        )
        for line in lines
    ]


class BaseTestCaseSegmentation(BaseTestCaseHtml):
    def setUp(self) -> None:
        super(BaseTestCaseSegmentation, self).setUp()
        self.make_text_spans = partial(_make_text_spans, self.soup)
