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
from arretify.semantic_tag_specs import SectionReferenceData, SectionReferenceSpec
from arretify.utils.testing import BaseTestCaseHtml, assert_element_lists_equal

from .sections_detection import parse_section_references


class TestArticleSingle(BaseTestCaseHtml):
    def test_article_num(self):
        # Arrange
        elements = ["article 4.1.b"]

        # Act
        actual = parse_section_references(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["article 4.1.b"],
                    data=SectionReferenceData(
                        type="article",
                        start_num="4.1.b",
                    ),
                ),
            ],
        )

    def test_article_8(self):
        # Arrange
        elements = ["article 8"]

        # Act
        actual = parse_section_references(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["article 8"],
                    data=SectionReferenceData(
                        type="article",
                        start_num="8",
                    ),
                ),
            ],
        )

    def test_article_1er(self):
        # Arrange
        elements = ["article 1er"]

        # Act
        actual = parse_section_references(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["article 1er"],
                    data=SectionReferenceData(
                        type="article",
                        start_num="1",
                    ),
                ),
            ],
        )

    def test_article_111e(self):
        # Arrange
        elements = ["article 111è"]

        # Act
        actual = parse_section_references(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["article 111è"],
                    data=SectionReferenceData(
                        type="article",
                        start_num="111",
                    ),
                ),
            ],
        )

    def test_article_2eme(self):
        # Arrange
        elements = ["article 2ème"]

        # Act
        actual = parse_section_references(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["article 2ème"],
                    data=SectionReferenceData(
                        type="article",
                        start_num="2",
                    ),
                ),
            ],
        )

    def test_code_article_r511_9(self):
        # Arrange
        elements = ["article R. 511-9"]

        # Act
        actual = parse_section_references(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["article R. 511-9"],
                    data=SectionReferenceData(
                        type="article",
                        start_num="R511-9",
                    ),
                ),
            ],
        )

    def test_code_article_d12(self):
        # Arrange
        elements = ["article D.12"]

        # Act
        actual = parse_section_references(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["article D.12"],
                    data=SectionReferenceData(
                        type="article",
                        start_num="D12",
                    ),
                ),
            ],
        )

    def test_code_article_l181_3(self):
        # Arrange
        elements = ["article L181-3"]

        # Act
        actual = parse_section_references(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["article L181-3"],
                    data=SectionReferenceData(
                        type="article",
                        start_num="L181-3",
                    ),
                ),
            ],
        )

    def test_ordinal_premier(self):
        # Arrange
        elements = ["article premier"]

        # Act
        actual = parse_section_references(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["article premier"],
                    data=SectionReferenceData(
                        type="article",
                        start_num="1",
                    ),
                ),
            ],
        )

    def test_ordinal_quatrieme(self):
        # Arrange
        elements = ["article quatrième"]

        # Act
        actual = parse_section_references(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["article quatrième"],
                    data=SectionReferenceData(
                        type="article",
                        start_num="4",
                    ),
                ),
            ],
        )

    def test_code_article_with_roman_subpart(self):
        # Arrange
        elements = ["article R 5125-8 - II - 2°"]

        # Act
        actual = parse_section_references(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["article R 5125-8 - II - 2°"],
                    data=SectionReferenceData(
                        type="article",
                        start_num="R5125-8",
                    ),
                ),
            ],
        )

    def test_code_article_with_roman_only(self):
        # Arrange
        elements = ["article L. 123-4 - IV"]

        # Act
        actual = parse_section_references(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["article L. 123-4 - IV"],
                    data=SectionReferenceData(
                        type="article",
                        start_num="L123-4",
                    ),
                ),
            ],
        )

    def test_code_article_with_degree_subpart(self):
        # Arrange
        elements = ["article D.12 - 3°"]

        # Act
        actual = parse_section_references(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["article D.12 - 3°"],
                    data=SectionReferenceData(
                        type="article",
                        start_num="D12",
                    ),
                ),
            ],
        )

    def test_ambiguous_paragraph_use(self):
        # Arrange
        elements = ["Paragraphe L123"]

        # Act
        actual = parse_section_references(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["Paragraphe L123"],
                    data=SectionReferenceData(
                        type="article",
                        start_num="L123",
                    ),
                ),
            ],
        )

    def test_dernier_adverb(self):
        # Arrange
        elements = ["le dernier article"]

        # Act
        actual = parse_section_references(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                "le",
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=[" dernier article"],
                    data=SectionReferenceData(
                        type="article",
                        start_num="-1",
                    ),
                ),
            ],
        )


class TestArticleMultiplicativeAdverb(BaseTestCaseHtml):

    def test_article_bis_with_space(self):
        # Arrange
        elements = ["article 5 bis"]

        # Act
        actual = parse_section_references(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["article 5 bis"],
                    data=SectionReferenceData(
                        type="article",
                        start_num="5bis",
                    ),
                ),
            ],
        )

    def test_article_ter_no_space(self):
        # Arrange
        elements = ["article 5.3.2.3ter"]

        # Act
        actual = parse_section_references(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["article 5.3.2.3ter"],
                    data=SectionReferenceData(
                        type="article",
                        start_num="5.3.2.3ter",
                    ),
                ),
            ],
        )

    def test_article_dotted_ter_with_space(self):
        # Arrange
        elements = ["article 5.3.2.3 ter"]

        # Act
        actual = parse_section_references(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["article 5.3.2.3 ter"],
                    data=SectionReferenceData(
                        type="article",
                        start_num="5.3.2.3ter",
                    ),
                ),
            ],
        )

    def test_article_code_quater(self):
        # Arrange
        elements = ["article L. 511-9 quater"]

        # Act
        actual = parse_section_references(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["article L. 511-9 quater"],
                    data=SectionReferenceData(
                        type="article",
                        start_num="L511-9quater",
                    ),
                ),
            ],
        )


class TestArticleRange(BaseTestCaseHtml):

    def test_article_num_range_3_to_11(self):
        # Arrange
        elements = ["articles 3 à 11"]

        # Act
        actual = parse_section_references(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["articles 3 à 11"],
                    data=SectionReferenceData(
                        type="article",
                        start_num="3",
                        end_num="11",
                    ),
                ),
            ],
        )

    def test_article_num_range_6_18_1_to_6_18_7(self):
        # Arrange
        elements = ["articles 6.18.1 à 6.18.7"]

        # Act
        actual = parse_section_references(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["articles 6.18.1 à 6.18.7"],
                    data=SectionReferenceData(
                        type="article",
                        start_num="6.18.1",
                        end_num="6.18.7",
                    ),
                ),
            ],
        )

    def test_article_num_range_6_18_a_to_6_18_c(self):
        # Arrange
        elements = ["articles 6.18.a à 6.18.c"]

        # Act
        actual = parse_section_references(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["articles 6.18.a à 6.18.c"],
                    data=SectionReferenceData(
                        type="article",
                        start_num="6.18.a",
                        end_num="6.18.c",
                    ),
                ),
            ],
        )

    def test_ordinal_range_premier_to_troisieme(self):
        # Arrange
        elements = ["de l'article premier à l'article troisième"]

        # Act
        actual = parse_section_references(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                "de l'",
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["article premier à l'article troisième"],
                    data=SectionReferenceData(
                        type="article",
                        start_num="1",
                        end_num="3",
                    ),
                ),
            ],
        )

    def test_ordinal_range_second_to_10eme(self):
        # Arrange
        elements = ["des articles second à 10ème"]

        # Act
        actual = parse_section_references(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                "des ",
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["articles second à 10ème"],
                    data=SectionReferenceData(
                        type="article",
                        start_num="2",
                        end_num="10",
                    ),
                ),
            ],
        )

    def test_code_article_range_r511_9_to_d512(self):
        # Arrange
        elements = ["de l'article R. 511-9 à l'article D.512"]

        # Act
        actual = parse_section_references(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                "de l'",
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["article R. 511-9 à l'article D.512"],
                    data=SectionReferenceData(
                        type="article",
                        start_num="R511-9",
                        end_num="D512",
                    ),
                ),
            ],
        )

    def test_code_article_range_r543_137_to_r543_151(self):
        # Arrange
        elements = ["l' article R.543-137 à R.543-151"]

        # Act
        actual = parse_section_references(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                "l' ",
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["article R.543-137 à R.543-151"],
                    data=SectionReferenceData(
                        type="article",
                        start_num="R543-137",
                        end_num="R543-151",
                    ),
                ),
            ],
        )


class TestArticlePlural(BaseTestCaseHtml):

    def test_article_num(self):
        # Arrange
        elements = ["articles 5.1.9, 9.2.1, 10.2.1 et 10.2.5"]

        # Act
        actual = parse_section_references(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["articles 5.1.9"],
                    data=SectionReferenceData(
                        type="article",
                        start_num="5.1.9",
                    ),
                    reserved_data_attrs=dict(group_id="1"),
                ),
                ", ",
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["9.2.1"],
                    data=SectionReferenceData(
                        type="article",
                        start_num="9.2.1",
                    ),
                    reserved_data_attrs=dict(group_id="1"),
                ),
                ", ",
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["10.2.1"],
                    data=SectionReferenceData(
                        type="article",
                        start_num="10.2.1",
                    ),
                    reserved_data_attrs=dict(group_id="1"),
                ),
                " et ",
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["10.2.5"],
                    data=SectionReferenceData(
                        type="article",
                        start_num="10.2.5",
                    ),
                    reserved_data_attrs=dict(group_id="1"),
                ),
            ],
        )

    def test_ordinal_premier_9a(self):
        # Arrange
        elements = ["articles premier,9.a"]

        # Act
        actual = parse_section_references(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["articles premier"],
                    data=SectionReferenceData(
                        type="article",
                        start_num="1",
                    ),
                    reserved_data_attrs=dict(group_id="1"),
                ),
                ",",
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["9.a"],
                    data=SectionReferenceData(
                        type="article",
                        start_num="9.a",
                    ),
                    reserved_data_attrs=dict(group_id="1"),
                ),
            ],
        )

    def test_ordinal_premier_et_second(self):
        # Arrange
        elements = ["articles premier et second"]

        # Act
        actual = parse_section_references(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["articles premier"],
                    data=SectionReferenceData(
                        type="article",
                        start_num="1",
                    ),
                    reserved_data_attrs=dict(group_id="1"),
                ),
                " et ",
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["second"],
                    data=SectionReferenceData(
                        type="article",
                        start_num="2",
                    ),
                    reserved_data_attrs=dict(group_id="1"),
                ),
            ],
        )

    def test_article_code(self):
        # Arrange
        elements = ["articles R. 511-9 et L. 111"]

        # Act
        actual = parse_section_references(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["articles R. 511-9"],
                    data=SectionReferenceData(
                        type="article",
                        start_num="R511-9",
                    ),
                    reserved_data_attrs=dict(group_id="1"),
                ),
                " et ",
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["L. 111"],
                    data=SectionReferenceData(
                        type="article",
                        start_num="L111",
                    ),
                    reserved_data_attrs=dict(group_id="1"),
                ),
            ],
        )

    def test_article_range(self):
        # Arrange
        elements = ["articles R. 512 - 74 et R. 512-39-1 à R.512-39-3"]

        # Act
        actual = parse_section_references(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["articles R. 512 - 74"],
                    data=SectionReferenceData(
                        type="article",
                        start_num="R512-74",
                    ),
                    reserved_data_attrs=dict(group_id="1"),
                ),
                " et ",
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["R. 512-39-1 à R.512-39-3"],
                    data=SectionReferenceData(
                        type="article",
                        start_num="R512-39-1",
                        end_num="R512-39-3",
                    ),
                    reserved_data_attrs=dict(group_id="1"),
                ),
            ],
        )

    def test_range_first(self):
        # Arrange
        elements = ["articles R.541-49 à R.541-64 et R.541-79"]

        # Act
        actual = parse_section_references(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["articles R.541-49 à R.541-64"],
                    data=SectionReferenceData(
                        type="article",
                        start_num="R541-49",
                        end_num="R541-64",
                    ),
                    reserved_data_attrs=dict(group_id="1"),
                ),
                " et ",
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["R.541-79"],
                    data=SectionReferenceData(
                        type="article",
                        start_num="R541-79",
                    ),
                    reserved_data_attrs=dict(group_id="1"),
                ),
            ],
        )


class TestAlineaSingle(BaseTestCaseHtml):

    def test_alinea_num_before(self):
        # Arrange
        elements = ["2ème alinéa"]

        # Act
        actual = parse_section_references(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["2ème alinéa"],
                    data=SectionReferenceData(
                        type="alinea",
                        start_num="2",
                    ),
                ),
            ],
        )

    def test_alinea_num_after_3(self):
        # Arrange
        elements = ["alinéa 3"]

        # Act
        actual = parse_section_references(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["alinéa 3"],
                    data=SectionReferenceData(
                        type="alinea",
                        start_num="3",
                    ),
                ),
            ],
        )

    def test_alinea_num_after_second(self):
        # Arrange
        elements = ["alinéa second"]

        # Act
        actual = parse_section_references(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["alinéa second"],
                    data=SectionReferenceData(
                        type="alinea",
                        start_num="2",
                    ),
                ),
            ],
        )

    def test_alinea_num_after_neuvieme(self):
        # Arrange
        elements = ["alinéa neuvième"]

        # Act
        actual = parse_section_references(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["alinéa neuvième"],
                    data=SectionReferenceData(
                        type="alinea",
                        start_num="9",
                    ),
                ),
            ],
        )

    def test_dernier_adverb(self):
        # Arrange
        elements = ["le dernier alinéa"]

        # Act
        actual = parse_section_references(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                "le",
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=[" dernier alinéa"],
                    data=SectionReferenceData(
                        type="alinea",
                        start_num="-1",
                    ),
                ),
            ],
        )


class TestAlineaRange(BaseTestCaseHtml):

    def test_alinea_num_range(self):
        # Arrange
        elements = ["alinéas 3 à 5"]

        # Act
        actual = parse_section_references(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["alinéas 3 à 5"],
                    data=SectionReferenceData(
                        type="alinea",
                        start_num="3",
                        end_num="5",
                    ),
                ),
            ],
        )

    def test_alinea_num_range_with_ordinal(self):
        # Arrange
        elements = ["alinéas premier à troisième"]

        # Act
        actual = parse_section_references(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["alinéas premier à troisième"],
                    data=SectionReferenceData(
                        type="alinea",
                        start_num="1",
                        end_num="3",
                    ),
                ),
            ],
        )


class TestAlineaMultiple(BaseTestCaseHtml):

    def test_alinea_list(self):
        # Arrange
        elements = ["Les alinéas 3 et 4"]

        # Act
        actual = parse_section_references(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                "Les ",
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["alinéas 3"],
                    data=SectionReferenceData(
                        type="alinea",
                        start_num="3",
                    ),
                    reserved_data_attrs=dict(group_id="1"),
                ),
                " et ",
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["4"],
                    data=SectionReferenceData(
                        type="alinea",
                        start_num="4",
                    ),
                    reserved_data_attrs=dict(group_id="1"),
                ),
            ],
        )


class TestUnknownSingle(BaseTestCaseHtml):

    def test_unknown_num(self):
        # Arrange
        elements = ["paragraphe 3"]

        # Act
        actual = parse_section_references(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["paragraphe 3"],
                    data=SectionReferenceData(
                        type="unknown",
                        start_num="3",
                    ),
                ),
            ],
        )

    def test_paragraph_symbol(self):
        # Arrange
        elements = ["Dans le § a.4"]

        # Act
        actual = parse_section_references(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                "Dans le ",
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["§ a.4"],
                    data=SectionReferenceData(
                        type="unknown",
                        start_num="a.4",
                    ),
                ),
            ],
        )


class TestUnknownRange(BaseTestCaseHtml):

    def test_unknown_num_range(self):
        # Arrange
        elements = ["paragraphes 3 à 5"]

        # Act
        actual = parse_section_references(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["paragraphes 3 à 5"],
                    data=SectionReferenceData(
                        type="unknown",
                        start_num="3",
                        end_num="5",
                    ),
                ),
            ],
        )


class TestUnknownMultiple(BaseTestCaseHtml):

    def test_paragraphe_list(self):
        # Arrange
        elements = ["Les paragraphes 3è, 5 et quatrième"]

        # Act
        actual = parse_section_references(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                "Les ",
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["paragraphes 3è"],
                    data=SectionReferenceData(
                        type="unknown",
                        start_num="3",
                    ),
                    reserved_data_attrs=dict(group_id="1"),
                ),
                ", ",
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["5"],
                    data=SectionReferenceData(
                        type="unknown",
                        start_num="5",
                    ),
                    reserved_data_attrs=dict(group_id="1"),
                ),
                " et ",
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["quatrième"],
                    data=SectionReferenceData(
                        type="unknown",
                        start_num="4",
                    ),
                    reserved_data_attrs=dict(group_id="1"),
                ),
            ],
        )


class TestTableSingle(BaseTestCaseHtml):

    def test_table_num_after(self):
        # Arrange
        elements = ["tableau 3"]

        # Act
        actual = parse_section_references(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["tableau 3"],
                    data=SectionReferenceData(
                        type="tableau",
                        start_num="3",
                    ),
                ),
            ],
        )

    def test_table_num_before(self):
        # Arrange
        elements = ["2ème tableau"]

        # Act
        actual = parse_section_references(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["2ème tableau"],
                    data=SectionReferenceData(
                        type="tableau",
                        start_num="2",
                    ),
                ),
            ],
        )

    def test_table_ordinal_premier_before(self):
        # Arrange
        elements = ["le premier tableau"]

        # Act
        actual = parse_section_references(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                "le ",
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["premier tableau"],
                    data=SectionReferenceData(
                        type="tableau",
                        start_num="1",
                    ),
                ),
            ],
        )

    def test_table_ordinal_after(self):
        # Arrange
        elements = ["tableau quatrième"]

        # Act
        actual = parse_section_references(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["tableau quatrième"],
                    data=SectionReferenceData(
                        type="tableau",
                        start_num="4",
                    ),
                ),
            ],
        )

    def test_table_no_number(self):
        # Arrange
        elements = ["le tableau de blabla"]

        # Act
        actual = parse_section_references(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                "le ",
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["tableau"],
                    data=SectionReferenceData(
                        type="tableau",
                    ),
                ),
                " de blabla",
            ],
        )

    def test_table_plural_no_number(self):
        # Arrange
        elements = ["sous les tableaux suivants"]

        # Act
        actual = parse_section_references(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                "sous les ",
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["tableaux"],
                    data=SectionReferenceData(
                        type="tableau",
                    ),
                ),
                " suivants",
            ],
        )

    def test_dernier_adverb(self):
        # Arrange
        elements = ["le dernier tableau"]

        # Act
        actual = parse_section_references(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                "le",
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=[" dernier tableau"],
                    data=SectionReferenceData(
                        type="tableau",
                        start_num="-1",
                    ),
                ),
            ],
        )


class TestAppendixSingle(BaseTestCaseHtml):

    def test_appendix_num(self):
        # Arrange
        elements = ["annexe 1"]

        # Act
        actual = parse_section_references(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["annexe 1"],
                    data=SectionReferenceData(
                        type="annexe",
                        start_num="1",
                    ),
                ),
            ],
        )

    def test_appendix_roman(self):
        # Arrange
        elements = ["annexe IV"]

        # Act
        actual = parse_section_references(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["annexe IV"],
                    data=SectionReferenceData(
                        type="annexe",
                        start_num="4",
                    ),
                ),
            ],
        )

    def test_appendix_no_number(self):
        # Arrange
        elements = ["en annexe de blabla"]

        # Act
        actual = parse_section_references(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                "en ",
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["annexe"],
                    data=SectionReferenceData(
                        type="annexe",
                    ),
                ),
                " de blabla",
            ],
        )
