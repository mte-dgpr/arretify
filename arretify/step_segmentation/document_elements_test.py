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
import unittest

from .document_elements import (
    initialize_document_structure,
    parse_tables_of_contents,
    render_table_of_contents,
)
from .testing import assert_elements_equal, make_text_spans
from arretify.utils.testing import create_document_context, normalized_html_str
from arretify.utils.html_semantic import make_semantic_tag
from arretify.semantic_tag_specs import PageSeparatorData, PageSeparatorSpec, TableOfContentsSpec
from .semantic_tag_specs import TextSpanData, TextSpanSpec


class BaseTestCase(unittest.TestCase):
    def setUp(self):
        self.context = create_document_context()
        self.soup = self.context.soup


class TestInitializeDocumentStructure(BaseTestCase):

    def test_page_separators_inserted_and_text_spans_created(self):
        # Arrange
        pages = [
            "Line 1\nLine 2\nLine 3",
            "Line 4\nLine 5",
            "Line 6",
        ]

        # Act
        result = initialize_document_structure(self.context, pages)

        # Assert
        assert_elements_equal(
            result,
            [
                make_semantic_tag(
                    self.soup, PageSeparatorSpec, data=PageSeparatorData(page_index=0)
                ),
                make_semantic_tag(
                    self.soup,
                    TextSpanSpec,
                    contents=["Line 1"],
                    data=TextSpanData(start=[0, 0, 0], end=[0, 0, 5]),
                ),
                make_semantic_tag(
                    self.soup,
                    TextSpanSpec,
                    contents=["Line 2"],
                    data=TextSpanData(start=[0, 1, 0], end=[0, 1, 5]),
                ),
                make_semantic_tag(
                    self.soup,
                    TextSpanSpec,
                    contents=["Line 3"],
                    data=TextSpanData(start=[0, 2, 0], end=[0, 2, 5]),
                ),
                make_semantic_tag(
                    self.soup, PageSeparatorSpec, data=PageSeparatorData(page_index=1)
                ),
                make_semantic_tag(
                    self.soup,
                    TextSpanSpec,
                    contents=["Line 4"],
                    data=TextSpanData(start=[1, 0, 0], end=[1, 0, 5]),
                ),
                make_semantic_tag(
                    self.soup,
                    TextSpanSpec,
                    contents=["Line 5"],
                    data=TextSpanData(start=[1, 1, 0], end=[1, 1, 5]),
                ),
                make_semantic_tag(
                    self.soup, PageSeparatorSpec, data=PageSeparatorData(page_index=2)
                ),
                make_semantic_tag(
                    self.soup,
                    TextSpanSpec,
                    contents=["Line 6"],
                    data=TextSpanData(start=[2, 0, 0], end=[2, 0, 5]),
                ),
            ],
        )


class TestParseTablesOfContents(BaseTestCase):

    def test_parse_tables_of_contents(self):
        # Arrange
        lines = make_text_spans(
            self.soup, "Line 1", "Sommaire", "bla ..... page 1", "blo ..... page 2", "Line 2"
        )

        # Act
        elements = parse_tables_of_contents(self.context, lines)

        # Assert
        assert_elements_equal(
            elements,
            [
                *make_text_spans(self.soup, "Line 1"),
                make_semantic_tag(
                    self.soup,
                    TableOfContentsSpec,
                    contents=make_text_spans(
                        self.soup,
                        "Sommaire",
                        "bla ..... page 1",
                        "blo ..... page 2",
                    ),
                ),
                *make_text_spans(self.soup, "Line 2"),
            ],
            ignore_text_span_data=True,
        )


class TestRenderTableOfContents(BaseTestCase):

    def test_simple_render(self):
        # Arrange
        tag = make_semantic_tag(
            self.soup,
            TableOfContentsSpec,
            contents=[
                make_semantic_tag(
                    self.soup,
                    TextSpanSpec,
                    contents=["Sommaire"],
                    data=TextSpanData(start=[0, 0, 0], end=[0, 0, 5]),
                ),
                make_semantic_tag(
                    self.soup,
                    TextSpanSpec,
                    contents=["bla ..... page 1"],
                    data=TextSpanData(start=[0, 1, 0], end=[0, 1, 5]),
                ),
                make_semantic_tag(
                    self.soup,
                    TextSpanSpec,
                    contents=["blo ..... page 2"],
                    data=TextSpanData(start=[0, 2, 0], end=[0, 2, 5]),
                ),
            ],
        )

        # Act
        rendered = render_table_of_contents(self.context, tag)

        # Assert
        assert normalized_html_str(str(rendered)) == normalized_html_str(
            """
            <div data-spec="table_of_contents">
                <div>Sommaire</div>
                <div>bla ..... page 1</div>
                <div>blo ..... page 2</div>
            </div>
        """
        )
