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

from arretify.regex_utils import PatternProxy
from arretify.semantic_tag_specs import AddressSpec, PageSeparatorData, PageSeparatorSpec
from arretify.utils.html_create import make_semantic_tag, make_tag
from arretify.utils.html_semantic import Contents, create_semantic_tag_spec_no_data
from arretify.utils.testing import create_document_context

from .core import (
    combine_text_spans,
    get_string,
    group_text_span_tags_splitter,
    make_pattern_splitter,
    make_probe_from_pattern_proxy,
    make_recombine_interrupted_lines_splitter,
    make_while_splitter_for_text_spans,
    pick_str,
    pick_text_spans,
)
from .semantic_tag_specs import (
    SEGMENTATION_TAG_NAME,
    TextSpanSegmentationData,
    TextSpanSegmentationSpec,
)
from .testing import assert_elements_equal, make_text_spans

SomeTagSpec = create_semantic_tag_spec_no_data(
    spec_name="segmentation:some_tag",
    tag_name=SEGMENTATION_TAG_NAME,
    allowed_contents=(
        Contents.Str(),
        Contents.SemanticTag(TextSpanSegmentationSpec.spec_name),
        Contents.Tag("some-tag"),
    ),
)


class BaseTestCase(unittest.TestCase):
    def setUp(self):
        self.context = create_document_context()
        self.soup = self.context.protected_soup


class TestMakeWhileSplitterForTextSpans(BaseTestCase):

    def test_rejects_non_text_span(self):
        # Arrange
        def probe(elements, index):
            return elements[index].contents[0].startswith("match")

        splitter = make_while_splitter_for_text_spans(
            probe,
            probe,
        )
        elements = [
            make_tag(self.soup, "some-tag"),
            *make_text_spans(self.soup, "match this"),
            make_tag(self.soup, "some-other-tag"),
        ]

        # Act
        result = splitter(elements)

        # Assert
        assert result == (elements[0:1], elements[1:2], elements[2:])

    def test_match_found(self):
        # Arrange
        def probe(elements, index):
            return elements[index].contents[0].startswith("match")

        splitter = make_while_splitter_for_text_spans(
            probe,
            probe,
        )
        elements = make_text_spans(self.soup, "no match", "match this", "match that", "no match")

        # Act
        result = splitter(elements)

        # Assert
        assert result == (elements[:1], elements[1:3], elements[3:])

    def test_start_is_matching_argument(self):
        # Arrange
        def start_condition(elements, index):
            return elements[index].contents[0] == "match this"

        def while_condition(elements, index):
            return elements[index].contents[0].startswith("match")

        splitter = make_while_splitter_for_text_spans(
            start_condition,
            while_condition,
        )
        elements = [
            make_tag(self.soup, "some-tag"),
            *make_text_spans(self.soup, "match this", "match that", "but not this"),
        ]

        # Act
        result = splitter(elements)

        # Assert
        assert result == (elements[:1], elements[1:3], elements[3:])

    def test_not_interrupted_by_transparent_tag(self):
        # Arrange
        def probe(elements, index):
            return elements[index].contents[0].startswith("match")

        splitter = make_while_splitter_for_text_spans(probe, probe)
        elements = [
            *make_text_spans(self.soup, "match this"),
            make_semantic_tag(self.soup, PageSeparatorSpec, data=PageSeparatorData(page_index=0)),
            *make_text_spans(self.soup, "match this too", "but not this"),
        ]

        # Act
        result = splitter(elements)

        # Assert
        assert result == ([], elements[0:3], elements[3:])


class TestGroupTextSpanTagsSplitter(BaseTestCase):

    def test_simple(self):
        # Arrange
        elements = [
            make_tag(self.soup, "some-tag"),
            make_semantic_tag(
                self.soup,
                TextSpanSegmentationSpec,
                contents=["line1"],
                data=TextSpanSegmentationData(start=[0, 0, 0], end=[0, 0, 0]),
            ),
            make_semantic_tag(
                self.soup,
                TextSpanSegmentationSpec,
                contents=["line2", "line3"],
                data=TextSpanSegmentationData(start=[0, 0, 0], end=[0, 0, 0]),
            ),
            make_tag(self.soup, "some-other-tag"),
        ]

        # Act
        result = group_text_span_tags_splitter(elements)

        # Assert
        assert result == (
            [
                make_tag(self.soup, "some-tag"),
            ],
            [
                make_semantic_tag(
                    self.soup,
                    TextSpanSegmentationSpec,
                    contents=["line1"],
                    data=TextSpanSegmentationData(start=[0, 0, 0], end=[0, 0, 0]),
                ),
                make_semantic_tag(
                    self.soup,
                    TextSpanSegmentationSpec,
                    contents=["line2", "line3"],
                    data=TextSpanSegmentationData(start=[0, 0, 0], end=[0, 0, 0]),
                ),
            ],
            [
                make_tag(self.soup, "some-other-tag"),
            ],
        )


class TestMakeProbeFromPatternProxy(BaseTestCase):

    def test_pattern_match(self):
        # Arrange
        pattern = PatternProxy(r"^match")
        probe = make_probe_from_pattern_proxy(pattern)
        lines = make_text_spans(self.soup, "match this")

        # Act
        result = probe(lines, 0)

        # Assert
        assert result is True

    def test_pattern_no_match(self):
        # Arrange
        pattern = PatternProxy(r"^match")
        probe = make_probe_from_pattern_proxy(pattern)
        lines = make_text_spans(self.soup, "no match here")

        # Act
        result = probe(lines, 0)

        # Assert
        assert result is False


class TestPickTextSpans(BaseTestCase):

    def test_simple(self):
        # Arrange
        elements = [
            make_semantic_tag(
                self.soup,
                TextSpanSegmentationSpec,
                contents=["bla1"],
                data=TextSpanSegmentationData(start=[0, 0, 0], end=[0, 0, 3]),
            ),
            make_tag(self.soup, "some-tag"),
            "bla2",
            make_semantic_tag(
                self.soup,
                TextSpanSegmentationSpec,
                contents=["blo4", "bla5"],
                data=TextSpanSegmentationData(start=[0, 0, 0], end=[0, 0, 3]),
            ),
        ]

        # Act
        text_spans_probe = pick_text_spans(lambda elements, index: True)

        # Assert
        assert text_spans_probe(elements, 0) is True
        assert text_spans_probe(elements, 1) is False
        assert text_spans_probe(elements, 2) is False
        assert text_spans_probe(elements, 3) is True


class TestPickStr(BaseTestCase):

    def test_simple(self):
        # Arrange
        elements = [
            "bla1",
            make_tag(self.soup, "some-tag"),
            "blo4",
        ]

        # Act
        probe = pick_str(lambda elements, index: True)

        # Assert
        assert probe(elements, 0) is True
        assert probe(elements, 1) is False
        assert probe(elements, 2) is True


class TestMakeRecombineInterruptedLinesSplitter(BaseTestCase):

    def test_multiple_lines_and_page_separators(self):
        # Arrange
        splitter = make_recombine_interrupted_lines_splitter(SomeTagSpec)
        elements = [
            make_semantic_tag(self.soup, SomeTagSpec, contents=["This is a line"]),
            make_semantic_tag(self.soup, PageSeparatorSpec, data=PageSeparatorData(page_index=1)),
            *make_text_spans(
                self.soup,
                " that continues ",
            ),
            make_semantic_tag(self.soup, PageSeparatorSpec, data=PageSeparatorData(page_index=2)),
            make_semantic_tag(self.soup, PageSeparatorSpec, data=PageSeparatorData(page_index=3)),
            *make_text_spans(
                self.soup,
                " and continues again.",
            ),
        ]

        # Act
        result = splitter(elements)

        # Assert
        assert result is not None
        before, match, after = result
        assert_elements_equal(before, [])
        assert_elements_equal(
            match,
            (
                make_semantic_tag(self.soup, SomeTagSpec, contents=["This is a line"]),
                make_semantic_tag(
                    self.soup, PageSeparatorSpec, data=PageSeparatorData(page_index=1)
                ),
                *make_text_spans(
                    self.soup,
                    " that continues ",
                ),
                make_semantic_tag(
                    self.soup, PageSeparatorSpec, data=PageSeparatorData(page_index=2)
                ),
                make_semantic_tag(
                    self.soup, PageSeparatorSpec, data=PageSeparatorData(page_index=3)
                ),
                *make_text_spans(
                    self.soup,
                    " and continues again.",
                ),
            ),
        )
        assert_elements_equal(after, [])

    def test_line_is_not_continuing(self):
        # Arrange
        splitter = make_recombine_interrupted_lines_splitter(SomeTagSpec)
        elements = [
            make_semantic_tag(self.soup, SomeTagSpec, contents=["This is a line."]),
            make_semantic_tag(self.soup, PageSeparatorSpec, data=PageSeparatorData(page_index=1)),
            *make_text_spans(
                self.soup,
                "blo blo blo",
            ),
        ]

        # Act
        result = splitter(elements)

        # Assert
        assert result is None

    def test_line_is_continuing_but_no_page_separator(self):
        # Arrange
        splitter = make_recombine_interrupted_lines_splitter(SomeTagSpec)
        elements = [
            make_semantic_tag(self.soup, SomeTagSpec, contents=["This is a line"]),
            *make_text_spans(self.soup, " that continues."),
        ]

        # Act
        result = splitter(elements)

        # Assert
        assert result is None


class TestGetString(BaseTestCase):

    def test_string(self):
        # Arrange
        string = "This is a test"

        # Act
        result = get_string(string)

        # Assert
        assert result == "This is a test"

    def test_tag_with_string_children(self):
        # Arrange
        tag = make_semantic_tag(self.soup, SomeTagSpec, contents=["This is", " a test"])

        # Act
        result = get_string(tag)

        # Assert
        assert result == "This is a test"

    def test_tag_with_text_spans(self):
        # Arrange
        tag = make_semantic_tag(
            self.soup,
            SomeTagSpec,
            contents=[
                "This is",
                make_semantic_tag(
                    self.soup,
                    TextSpanSegmentationSpec,
                    contents=[" a test"],
                    data=TextSpanSegmentationData(start=[0, 0, 0], end=[0, 0, 5]),
                ),
            ],
        )

        # Act
        result = get_string(tag)

        # Assert
        assert result == "This is a test"

    def test_tag_with_non_text_child(self):
        # Arrange
        tag = make_semantic_tag(
            self.soup,
            SomeTagSpec,
            contents=[
                "This is",
                make_tag(self.soup, "some-tag"),
                " a test",
            ],
        )

        # Assert
        with self.assertRaises(ValueError):
            get_string(tag)

    def test_inline_tags_inside_text_span(self):
        # Arrange
        tag = make_semantic_tag(
            self.soup,
            TextSpanSegmentationSpec,
            contents=[
                "Viens au ",
                make_semantic_tag(self.soup, AddressSpec, contents=["123 rue de la Paix"]),
                ", à 12h",
            ],
            data=TextSpanSegmentationData(start=[0, 0, 0], end=[0, 0, 0]),
        )

        # Act
        result = get_string(tag)

        # Assert
        assert result == "Viens au 123 rue de la Paix, à 12h"


class TestCombineTextSpans(BaseTestCase):

    def test_combine_text_spans(self):
        # Arrange
        elements = [
            make_semantic_tag(
                self.soup,
                TextSpanSegmentationSpec,
                contents=["This is"],
                data=TextSpanSegmentationData(start=[1, 2, 3], end=[4, 5, 6]),
            ),
            make_semantic_tag(
                self.soup,
                TextSpanSegmentationSpec,
                contents=[" a test", " with multiple lines."],
                data=TextSpanSegmentationData(start=[7, 8, 9], end=[16, 17, 18]),
            ),
        ]

        # Act
        result = combine_text_spans(self.context, elements)

        # Assert
        assert_elements_equal(
            [result],
            [
                make_semantic_tag(
                    self.soup,
                    TextSpanSegmentationSpec,
                    contents=[
                        "This is",
                        " a test",
                        " with multiple lines.",
                    ],
                    data=TextSpanSegmentationData(start=[1, 2, 3], end=[16, 17, 18]),
                )
            ],
        )

    def test_containing_inline_tag(self):
        # Arrange
        elements = [
            make_semantic_tag(
                self.soup,
                TextSpanSegmentationSpec,
                contents=["This is"],
                data=TextSpanSegmentationData(start=[1, 2, 3], end=[4, 5, 6]),
            ),
            make_semantic_tag(
                self.soup,
                TextSpanSegmentationSpec,
                contents=[
                    " a test ",
                    make_semantic_tag(self.soup, AddressSpec, contents=["123 rue de la Paix"]),
                    " with multiple lines.",
                ],
                data=TextSpanSegmentationData(start=[7, 8, 9], end=[16, 17, 18]),
            ),
        ]

        # Act
        result = combine_text_spans(self.context, elements)

        # Assert
        assert_elements_equal(
            [result],
            [
                make_semantic_tag(
                    self.soup,
                    TextSpanSegmentationSpec,
                    contents=[
                        "This is",
                        " a test ",
                        make_semantic_tag(self.soup, AddressSpec, contents=["123 rue de la Paix"]),
                        " with multiple lines.",
                    ],
                    data=TextSpanSegmentationData(start=[1, 2, 3], end=[16, 17, 18]),
                )
            ],
        )


class TestMakePatternSplitter(BaseTestCase):

    def test_match_middle(self):
        # Arrange
        pattern = PatternProxy(r"\d+")
        splitter = make_pattern_splitter(pattern)
        elements = [
            "abc",
            make_tag(self.soup, "some-tag"),
            "def123ghi",
            make_tag(self.soup, "some-tag"),
            "jkl",
        ]

        # Act
        result = splitter(elements)

        # Assert
        assert result is not None
        before, match, after = result
        assert_elements_equal(
            before,
            [
                "abc",
                make_tag(self.soup, "some-tag"),
                "def",
            ],
        )
        assert_elements_equal(
            after,
            [
                "ghi",
                make_tag(self.soup, "some-tag"),
                "jkl",
            ],
        )
        assert match.group(0) == "123"

    def test_match_start(self):
        # Arrange
        pattern = PatternProxy(r"\d+")
        splitter = make_pattern_splitter(pattern)
        elements = ["123abc"]

        # Act
        result = splitter(elements)

        # Assert
        assert result is not None
        before, match, after = result
        assert_elements_equal(before, [])
        assert_elements_equal(after, ["abc"])
        assert match.group(0) == "123"

    def test_match_end(self):
        # Arrange
        pattern = PatternProxy(r"\d+")
        splitter = make_pattern_splitter(pattern)
        elements = ["jkl456"]

        # Act
        result = splitter(elements)

        # Assert
        assert result is not None
        before, match, after = result
        assert_elements_equal(before, ["jkl"])
        assert_elements_equal(after, [])
        assert match.group(0) == "456"

    def test_no_match(self):
        # Arrange
        pattern = PatternProxy(r"\d+")
        splitter = make_pattern_splitter(pattern)
        elements = ["abc", "defghi", "jkl"]

        # Act
        result = splitter(elements)

        # Assert
        assert result is None

    def test_match_across_segments(self):
        # Arrange
        pattern = PatternProxy(r"defghi")
        splitter = make_pattern_splitter(pattern)
        elements = ["abcdef", "ghijkl"]

        # Act
        result = splitter(elements)

        # Assert
        assert result is not None
        before, match, after = result
        assert_elements_equal(before, ["abc"])
        assert_elements_equal(after, ["jkl"])
        assert match.group(0) == "defghi"
