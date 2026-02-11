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

from arretify.semantic_tag_specs import (
    AppendixSpec,
    ArreteData,
    ArreteSpec,
    MainSpec,
    SectionData,
    SectionSpec,
)
from arretify.utils.testing import BaseTestCaseHtml
from quality_evaluation.segmentation_in_sections import (
    SectionTree,
    SectionTreeNode,
    _generate_string_for_section_tree,
    _generate_string_for_section_tree_node_list,
    _normalize_section_tree_string,
    build_section_tree,
    compute_metric_scores,
)


class TestGenerateStringForSectionTreeNodeList(unittest.TestCase):
    def test_nested_children(self):
        # Arrange
        children = [
            SectionTreeNode(
                data=SectionData(number="1", title="Section 1", type="article"),
                children=[
                    SectionTreeNode(
                        data=SectionData(number="1.1", title="Section 1.1", type="article"),
                        children=[],
                    ),
                ],
            )
        ]

        # Act
        result = _generate_string_for_section_tree_node_list(children)

        # Assert
        assert result == "1\n>1.1\n"


class TestGenerateStringForSectionTree(unittest.TestCase):
    def test_main_and_appendix(self):
        # Arrange
        section_tree = SectionTree(
            main=[
                SectionTreeNode(
                    data=SectionData(number="1", title="Article 1", type="article"),
                    children=[],
                ),
                SectionTreeNode(
                    data=SectionData(number="2", title="Article 2", type="article"),
                    children=[],
                ),
            ],
            appendix=[
                SectionTreeNode(
                    data=SectionData(number="A", title="Annexe A", type="annexe"),
                    children=[],
                ),
            ],
        )

        # Act
        string = _generate_string_for_section_tree(section_tree)

        # Assert
        assert string == "1\n2\n-\nA"


class TestNormalizeSectionTreeString(unittest.TestCase):
    def test_pads_lines_to_max_length(self):
        # Arrange
        section_tree_string = "1\n10.5.3\n2"

        # Act
        result = _normalize_section_tree_string(section_tree_string)

        # Assert
        lines = result.splitlines()
        assert len(lines) == 3
        assert all(len(line) == 6 for line in lines)
        assert lines[0] == "1     "
        assert lines[1] == "10.5.3"
        assert lines[2] == "2     "


class TestBuildSectionTree(BaseTestCaseHtml):

    def test_nested_sections(self):
        # Arrange
        arrete_tag = self.make_semantic_tag(
            ArreteSpec,
            data=ArreteData(arretify_version="test-version"),
            contents=[
                self.make_semantic_tag(
                    MainSpec,
                    contents=[
                        self.make_semantic_tag(
                            SectionSpec,
                            data=SectionData(number="1", title="Section 1", type="article"),
                            contents=[
                                self.make_semantic_tag(
                                    SectionSpec,
                                    data=SectionData(
                                        number="1.1", title="Section 1.1", type="article"
                                    ),
                                )
                            ],
                        )
                    ],
                )
            ],
        )
        self.soup.append(arrete_tag)

        # Act
        result = build_section_tree(self.context)

        # Assert
        assert len(result.main) == 1
        assert result.main[0].data.number == "1"
        assert len(result.main[0].children) == 1
        assert result.main[0].children[0].data.number == "1.1"

    def test_with_appendix(self):
        # Arrange
        arrete_tag = self.make_semantic_tag(
            ArreteSpec,
            data=ArreteData(arretify_version="test-version"),
            contents=[
                self.make_semantic_tag(
                    MainSpec,
                    contents=[
                        self.make_semantic_tag(
                            SectionSpec,
                            data=SectionData(number="1", title="Article 1", type="article"),
                        )
                    ],
                ),
                self.make_semantic_tag(
                    AppendixSpec,
                    contents=[
                        self.make_semantic_tag(
                            SectionSpec,
                            data=SectionData(number="A", title="Annexe A", type="annexe"),
                        )
                    ],
                ),
            ],
        )
        self.soup.append(arrete_tag)

        # Act
        result = build_section_tree(self.context)

        # Assert
        assert len(result.main) == 1
        assert result.main[0].data.number == "1"
        assert result.appendix is not None
        assert len(result.appendix) == 1
        assert result.appendix[0].data.number == "A"


class TestComputeMetricScores(unittest.TestCase):
    def test_compute_metric_scores_without_diff(self):
        # Arrange
        ground_truth = SectionTree(
            main=[
                SectionTreeNode(data=SectionData(number="1", type="titre"), children=[]),
            ],
            appendix=None,
        )
        result = SectionTree(
            main=[
                SectionTreeNode(data=SectionData(number="1", type="titre"), children=[]),
            ],
            appendix=None,
        )

        # Act
        metric_scores, (string_result, string_ground_truth) = compute_metric_scores(
            section_tree_result=result,
            section_tree_ground_truth=ground_truth,
        )

        # Assert
        assert metric_scores["sections_similarity"] == 1.0
        assert string_result == string_ground_truth

    def test_compute_metric_scores_with_diff(self):
        # Arrange
        ground_truth = SectionTree(
            main=[
                SectionTreeNode(data=SectionData(number="1", type="titre"), children=[]),
            ],
            appendix=None,
        )
        result = SectionTree(
            main=[
                SectionTreeNode(data=SectionData(number="2", type="titre"), children=[]),
            ],
            appendix=None,
        )

        # Act
        metric_scores, (string_result, string_ground_truth) = compute_metric_scores(
            section_tree_result=result,
            section_tree_ground_truth=ground_truth,
        )

        # Assert
        assert metric_scores["sections_similarity"] < 1.0
        assert string_result != string_ground_truth
        assert "1" in string_ground_truth
        assert "2" in string_result
