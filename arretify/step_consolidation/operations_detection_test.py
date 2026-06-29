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

from arretify.semantic_tag_specs import OperationData, OperationSpec, SectionReferenceSpec
from arretify.utils.testing import BaseTestCaseHtml, assert_element_lists_equal

from .operations_detection import parse_operations


class TestParseOperations(BaseTestCaseHtml):
    def test_with_other_tags_left_and_right(self):
        # Arrange
        elements = [
            self.make_semantic_tag(
                SectionReferenceSpec,
                contents=["L'article 1.2.3"],
            ),
            "est remplacé par les dispositions suivantes :",
            self.make_semantic_tag(
                SectionReferenceSpec, contents=["l'article 4.5.6 du présent arrêté"]
            ),
        ]

        # Act
        actual = parse_operations(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["L'article 1.2.3"],
                ),
                self.make_semantic_tag(
                    OperationSpec,
                    contents=[
                        "est ",
                        self.make_tag("b", contents=["remplacé"]),
                        " par les dispositions suivantes :",
                    ],
                    data=OperationData(
                        operation_type="replace",
                        has_operand="true",
                        keyword="remplacé",
                        direction="rtl",
                    ),
                ),
                self.make_semantic_tag(
                    SectionReferenceSpec, contents=["l'article 4.5.6 du présent arrêté"]
                ),
            ],
        )

    def test_with_text_before(self):
        # Arrange
        elements = [
            self.make_semantic_tag(
                SectionReferenceSpec,
                contents=["L'article 1.2.3"],
            ),
            "portant sur les microplastiques est remplacé par les dispositions suivantes :",
        ]

        # Act
        actual = parse_operations(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    SectionReferenceSpec,
                    contents=["L'article 1.2.3"],
                ),
                self.make_semantic_tag(
                    OperationSpec,
                    contents=[
                        "portant sur les microplastiques est ",
                        self.make_tag("b", contents=["remplacé"]),
                        " par les dispositions suivantes :",
                    ],
                    data=OperationData(
                        operation_type="replace",
                        has_operand="true",
                        keyword="remplacé",
                        direction="rtl",
                    ),
                ),
            ],
        )


class TestReplaceOperations(BaseTestCaseHtml):

    def test_has_operand(self):
        # Arrange
        elements = ["sont remplacées comme suit :"]

        # Act
        actual = parse_operations(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    OperationSpec,
                    contents=[
                        "sont ",
                        self.make_tag("b", contents=["remplacées"]),
                        " comme suit :",
                    ],
                    data=OperationData(
                        operation_type="replace",
                        has_operand="true",
                        keyword="remplacées",
                        direction="rtl",
                    ),
                ),
            ],
        )

    def test_canceled_and_replaced(self):
        # Arrange
        elements = [
            (
                "Les prescriptions suivantes sont annulées et remplacées par les "
                "dispositions du présent arrêté :"
            )
        ]

        # Act
        actual = parse_operations(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    OperationSpec,
                    contents=[
                        "Les prescriptions suivantes sont ",
                        self.make_tag("b", contents=["annulées et remplacées"]),
                        " par les dispositions du présent arrêté :",
                    ],
                    data=OperationData(
                        operation_type="replace",
                        has_operand="true",
                        keyword="annulées et remplacées",
                        direction="rtl",
                    ),
                ),
            ],
        )

    def test_revoked_and_replaced(self):
        # Arrange
        elements = [
            "Les prescriptions de cet article sont abrogées et remplacées par celles ci-après :"
        ]

        # Act
        actual = parse_operations(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    OperationSpec,
                    contents=[
                        "Les prescriptions de cet article sont ",
                        self.make_tag("b", contents=["abrogées et remplacées"]),
                        " par celles ci-après :",
                    ],
                    data=OperationData(
                        operation_type="replace",
                        has_operand="true",
                        keyword="abrogées et remplacées",
                        direction="rtl",
                    ),
                ),
            ],
        )

    def test_deleted_and_replaced(self):
        # Arrange
        elements = [
            "L' article 1 .2 .2 SITUATION DE L'ÉTABLISSEMENT est supprimé et remplacé par :"
        ]

        # Act
        actual = parse_operations(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    OperationSpec,
                    contents=[
                        "L' article 1 .2 .2 SITUATION DE L'ÉTABLISSEMENT est ",
                        self.make_tag("b", contents=["supprimé et remplacé"]),
                        " par :",
                    ],
                    data=OperationData(
                        operation_type="replace",
                        has_operand="true",
                        keyword="supprimé et remplacé",
                        direction="rtl",
                    ),
                ),
            ],
        )

    def test_modified_and_replaced(self):
        # Arrange
        elements = [
            "2 .4 .2 L' article 15 .2 de l' arrêté préfectoral du 19 mars 2003 "
            "est modifié et remplacé par les dispositions suivantes :"
        ]

        # Act
        actual = parse_operations(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    OperationSpec,
                    contents=[
                        "2 .4 .2 L' article 15 .2 de l' arrêté préfectoral du 19 mars 2003 est ",
                        self.make_tag("b", contents=["modifié et remplacé"]),
                        " par les dispositions suivantes :",
                    ],
                    data=OperationData(
                        operation_type="replace",
                        has_operand="true",
                        keyword="modifié et remplacé",
                        direction="rtl",
                    ),
                ),
            ],
        )

    def test_modified_and_completed_by(self):
        # Arrange
        elements = [
            "L'article 5 des prescriptions techniques annexées à l'arrêté préfectoral du "
            "11 juin 2004 est modifié et complété par les dispositions suivantes :"
        ]

        # Act
        actual = parse_operations(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    OperationSpec,
                    contents=[
                        (
                            "L'article 5 des prescriptions techniques annexées à l'arrêté "
                            "préfectoral du 11 juin 2004 est "
                        ),
                        self.make_tag("b", contents=["modifié et complété"]),
                        " par les dispositions suivantes :",
                    ],
                    data=OperationData(
                        operation_type="replace",
                        has_operand="true",
                        keyword="modifié et complété",
                        direction="rtl",
                    ),
                ),
            ],
        )

    def test_modified_completed_or_annulled(self):
        # Arrange
        elements = [
            "Les dispositions de l'arrêté préfectoral n09-0150 du 20 janvier 2009 susvisé "
            "sont modifiées, complétées, ou annulées par les dispositions fixées aux articles "
            "suivants, et dont le récapitulatif figure ci-après :"
        ]

        # Act
        actual = parse_operations(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    OperationSpec,
                    contents=[
                        (
                            "Les dispositions de l'arrêté préfectoral n09-0150 du 20 janvier "
                            "2009 susvisé sont "
                        ),
                        self.make_tag("b", contents=["modifiées, complétées, ou annulées"]),
                        (
                            " par les dispositions fixées aux articles suivants, et dont le "
                            "récapitulatif figure ci-après :"
                        ),
                    ],
                    data=OperationData(
                        operation_type="replace",
                        has_operand="true",
                        keyword="modifiées, complétées, ou annulées",
                        direction="rtl",
                    ),
                ),
            ],
        )

    def test_modified_simple_disposition(self):
        # Arrange
        elements = [
            "La dernière phrase de l'article 8.1.1.2 de l'arrêté préfectoral du 10 décembre 2008 "
            "est remplacée par la disposition suivante :"
        ]

        # Act
        actual = parse_operations(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    OperationSpec,
                    contents=[
                        (
                            "La dernière phrase de l'article 8.1.1.2 de l'arrêté préfectoral "
                            "du 10 décembre 2008 est "
                        ),
                        self.make_tag("b", contents=["remplacée"]),
                        " par la disposition suivante :",
                    ],
                    data=OperationData(
                        operation_type="replace",
                        has_operand="true",
                        keyword="remplacée",
                        direction="rtl",
                    ),
                ),
            ],
        )

    def test_modified_operand(self):
        # Arrange
        elements = [
            "La dernière phrase de l'article 8.1.1.2 de l'arrêté préfectoral du 10 décembre 2008 "
            "est ainsi modifiée :"
        ]

        # Act
        actual = parse_operations(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    OperationSpec,
                    contents=[
                        (
                            "La dernière phrase de l'article 8.1.1.2 de l'arrêté préfectoral "
                            "du 10 décembre 2008 est ainsi "
                        ),
                        self.make_tag("b", contents=["modifiée"]),
                        " :",
                    ],
                    data=OperationData(
                        operation_type="replace",
                        has_operand="true",
                        keyword="modifiée",
                        direction="rtl",
                    ),
                ),
            ],
        )

    def test_delete_replace_plural(self):
        # Arrange
        elements = [
            "Les dispositions de l'article 2.8 - Arrêtés types sont supprimées et sont remplacées "
            "par celles du tableau suivant :"
        ]

        # Act
        actual = parse_operations(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    OperationSpec,
                    contents=[
                        "Les dispositions de l'article 2.8 - Arrêtés types sont ",
                        self.make_tag("b", contents=["supprimées et sont remplacées"]),
                        " par celles du tableau suivant :",
                    ],
                    data=OperationData(
                        operation_type="replace",
                        has_operand="true",
                        keyword="supprimées et sont remplacées",
                        direction="rtl",
                    ),
                ),
            ],
        )

    def test_update(self):
        # Arrange
        elements = [
            "Le tableau de l'article 1.2.1 de l'arrêté préfectoral du 10 décembre 2008 "
            "est mis à jour de la façon suivante :"
        ]

        # Act
        actual = parse_operations(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    OperationSpec,
                    contents=[
                        (
                            "Le tableau de l'article 1.2.1 de l'arrêté préfectoral du 10 "
                            "décembre 2008 est "
                        ),
                        self.make_tag("b", contents=["mis à jour"]),
                        " de la façon suivante :",
                    ],
                    data=OperationData(
                        operation_type="replace",
                        has_operand="true",
                        keyword="mis à jour",
                        direction="rtl",
                    ),
                ),
            ],
        )


class TestAddOperations(BaseTestCaseHtml):
    def test_add_completed_as_follows(self):
        # Arrange
        elements = [
            "Le paragraphe 4.14 - Postes de chargement -déchargement est complété comme suit :"
        ]

        # Act
        actual = parse_operations(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    OperationSpec,
                    contents=[
                        "Le paragraphe 4.14 - Postes de chargement -déchargement est ",
                        self.make_tag("b", contents=["complété"]),
                        " comme suit :",
                    ],
                    data=OperationData(
                        operation_type="add",
                        has_operand="true",
                        keyword="complété",
                        direction="rtl",
                    ),
                ),
            ],
        )

    def test_add_completed(self):
        # Arrange
        elements = ["Le paragraphe 4.19.1 - Réseau d'eau incendie est complété ainsi"]

        # Act
        actual = parse_operations(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    OperationSpec,
                    contents=[
                        "Le paragraphe 4.19.1 - Réseau d'eau incendie est ",
                        self.make_tag("b", contents=["complété"]),
                        " ainsi",
                    ],
                    data=OperationData(
                        operation_type="add",
                        keyword="complété",
                        direction="rtl",
                        has_operand=True,
                    ),
                ),
            ],
        )

    def test_completed_d_multiple_articles(self):
        # Arrange
        elements = [
            "Les prescriptions de l' article 8.3. dispositions spécifiques à l'installation de "
            "combustion de l' arrêté préfectoral du 15 mars 2013 sont complétés d' articles 8.3 .8 "
            "et 8.3 .9 ainsi rédigés :"
        ]

        # Act
        actual = parse_operations(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    OperationSpec,
                    contents=[
                        (
                            "Les prescriptions de l' article 8.3. dispositions spécifiques à "
                            "l'installation de combustion de l' arrêté préfectoral du 15 mars "
                            "2013 sont "
                        ),
                        self.make_tag("b", contents=["complétés"]),
                        " d'",
                    ],
                    data=OperationData(
                        operation_type="add",
                        keyword="complétés",
                        direction="rtl",
                    ),
                ),
                " articles 8.3 .8 et 8.3 .9 ainsi rédigés :",
            ],
        )

    def test_add_operation(self):
        # Arrange
        elements = ["Il est créé un article 4.3.14 à l'arrêté préfectoral du 10 décembre 2008"]

        # Act
        actual = parse_operations(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    OperationSpec,
                    contents=["Il est ", self.make_tag("b", contents=["créé"]), " un "],
                    data=OperationData(
                        operation_type="add",
                        keyword="créé",
                        direction="rtl",
                    ),
                ),
                "article 4.3.14 à l'arrêté préfectoral du 10 décembre 2008",
            ],
        )

    def test_created_article_end(self):
        # Arrange
        elements = [
            "Un article additionnel 8.2.5 relatif au fonctionnement du casier VIII en mode "
            "bioréacteur est créé en fin de chapitre 8.2 intitulé Zone de stockage de déchets non"
            "dangereux de l' arrêté préfectoral du 28 novembre 2017"
        ]

        # Act
        actual = parse_operations(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    OperationSpec,
                    contents=[
                        (
                            "Un article additionnel 8.2.5 relatif au fonctionnement du casier "
                            "VIII en mode bioréacteur est "
                        ),
                        self.make_tag("b", contents=["créé"]),
                        " en fin de ",
                    ],
                    data=OperationData(
                        operation_type="add",
                        keyword="créé",
                        direction="rtl",
                    ),
                ),
                (
                    "chapitre 8.2 intitulé Zone de stockage de déchets nondangereux de "
                    "l' arrêté préfectoral du 28 novembre 2017"
                ),
            ],
        )

    def test_created_new_chapter(self):
        # Arrange
        elements = [
            (
                "Il est créé un nouveau chapitre 11.6 à l' arrêté du 16 juillet 2010 "
                "rédigé comme suit :"
            )
        ]

        # Act
        actual = parse_operations(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    OperationSpec,
                    contents=["Il est ", self.make_tag("b", contents=["créé"]), " un nouveau "],
                    data=OperationData(
                        operation_type="add",
                        keyword="créé",
                        direction="rtl",
                    ),
                ),
                "chapitre 11.6 à l' arrêté du 16 juillet 2010 rédigé comme suit :",
            ],
        )

    def test_created_new_article(self):
        # Arrange
        elements = [
            "Il est créé un nouvel article 8.2.3 à l' arrêté du 16 juillet 2010 rédigé comme suit :"
        ]

        # Act
        actual = parse_operations(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    OperationSpec,
                    contents=["Il est ", self.make_tag("b", contents=["créé"]), " un nouvel "],
                    data=OperationData(
                        operation_type="add",
                        keyword="créé",
                        direction="rtl",
                    ),
                ),
                "article 8.2.3 à l' arrêté du 16 juillet 2010 rédigé comme suit :",
            ],
        )

    def test_created_two_new_articles(self):
        # Arrange
        elements = [
            (
                "Sous le tableau de la liste des activités autorisées, il est créé "
                "deux nouveaux articles ainsi rédigés :"
            )
        ]

        # Act
        actual = parse_operations(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    OperationSpec,
                    contents=[
                        "Sous le tableau de la liste des activités autorisées, il est ",
                        self.make_tag("b", contents=["créé"]),
                        " deux nouveaux articles ainsi rédigés :",
                    ],
                    data=OperationData(
                        operation_type="add",
                        has_operand="true",
                        keyword="créé",
                        direction="rtl",
                    ),
                ),
            ],
        )

    def test_add_operation_(self):
        # Arrange
        elements = [
            (
                "Paragraphe 4.25 -Cuyes de stockages de TDI/MOI. Il est ajouté un "
                "paragraphe rédigé ainsi:"
            )
        ]

        # Act
        actual = parse_operations(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    OperationSpec,
                    contents=[
                        "Paragraphe 4.25 -Cuyes de stockages de TDI/MOI. Il est ",
                        self.make_tag("b", contents=["ajouté"]),
                        " un paragraphe rédigé ainsi:",
                    ],
                    data=OperationData(
                        operation_type="add",
                        has_operand="true",
                        keyword="ajouté",
                        direction="rtl",
                    ),
                ),
            ],
        )

    def test_add_operation_with_article_references(self):
        # Arrange
        elements = ["L' article 8 .6 suivant est ajouté à l'arrêté préfectoral"]

        # Act
        actual = parse_operations(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    OperationSpec,
                    contents=[
                        "L' article 8 .6 suivant est ",
                        self.make_tag("b", contents=["ajouté"]),
                        " à l'arrêté préfectoral",
                    ],
                    data=OperationData(
                        operation_type="add",
                        has_operand="true",
                        keyword="ajouté",
                        direction="rtl",
                    ),
                ),
            ],
        )

    def test_modified_by_addition_operation(self):
        # Arrange
        elements = [
            "Le chapitre 6.7 relatif aux déchets produits par l'établissement de l'arrêté "
            "préfectoral d'autorisation du 08 décembre 2009 est modifié par l'ajout du paragraphe"
        ]

        # Act
        actual = parse_operations(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    OperationSpec,
                    contents=[
                        (
                            "Le chapitre 6.7 relatif aux déchets produits par l'établissement "
                            "de l'arrêté préfectoral d'autorisation du 08 décembre 2009 est "
                        ),
                        self.make_tag("b", contents=["modifié par l'ajout"]),
                        " du paragraphe",
                    ],
                    data=OperationData(
                        operation_type="add",
                        has_operand="true",
                        keyword="modifié par l'ajout",
                        direction="rtl",
                    ),
                ),
            ],
        )

    def test_insert_paragraph_at_start(self):
        # Arrange
        elements = ["2.4.3 Le paragraphe suivant est inséré au début de l' article 15.4"]

        # Act
        actual = parse_operations(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    OperationSpec,
                    contents=[
                        "2.4.3 Le paragraphe suivant est ",
                        self.make_tag("b", contents=["inséré"]),
                        " au début de ",
                    ],
                    data=OperationData(
                        operation_type="add",
                        keyword="inséré",
                        direction="rtl",
                    ),
                ),
                "l' article 15.4",
            ],
        )

    def test_insert_after_alinea(self):
        # Arrange
        elements = [
            (
                "A la suite du 1er  alinéa de l' article 14.5 de l' arrêté préfectoral "
                "du 18 avril 2005 sont insérées les dispositions suivantes :"
            )
        ]

        # Act
        actual = parse_operations(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    OperationSpec,
                    contents=[
                        (
                            "A la suite du 1er  alinéa de l' article 14.5 de l' arrêté "
                            "préfectoral du 18 avril 2005 sont "
                        ),
                        self.make_tag("b", contents=["insérées"]),
                        " les dispositions suivantes :",
                    ],
                    data=OperationData(
                        operation_type="add",
                        has_operand="true",
                        keyword="insérées",
                        direction="rtl",
                    ),
                ),
            ],
        )

    def test_insert_new_alinea_after(self):
        # Arrange
        elements = [
            "Après le 4ème alinéa de l'article 4.3.8 de l'arrêté préfectoral précité, "
            "il est inséré le nouvel alinéa suivant :"
        ]

        # Act
        actual = parse_operations(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    OperationSpec,
                    contents=[
                        (
                            "Après le 4ème alinéa de l'article 4.3.8 de l'arrêté préfectoral "
                            "précité, il est "
                        ),
                        self.make_tag("b", contents=["inséré"]),
                        " le nouvel alinéa suivant :",
                    ],
                    data=OperationData(
                        operation_type="add",
                        has_operand="true",
                        keyword="inséré",
                        direction="rtl",
                    ),
                ),
            ],
        )

    def test_insert_two_new_alinea(self):
        # Arrange
        elements = [
            "Après lé 6ème alinéa de l'article 4.3.8 de l'arrêté préfectoral précité, "
            "il est inséré les deux nouveaux alinéas suivants :"
        ]

        # Act
        actual = parse_operations(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    OperationSpec,
                    contents=[
                        (
                            "Après lé 6ème alinéa de l'article 4.3.8 de l'arrêté préfectoral "
                            "précité, il est "
                        ),
                        self.make_tag("b", contents=["inséré"]),
                        " les deux nouveaux alinéas suivants :",
                    ],
                    data=OperationData(
                        operation_type="add",
                        has_operand="true",
                        keyword="inséré",
                        direction="rtl",
                    ),
                ),
            ],
        )

    def test_insert_article_after(self):
        # Arrange
        elements = [
            (
                "Un article numéroté 7.7.6.3. est inséré à la suite de l' article 7.7.6.2. "
                "des prescriptions annexées à l' arrêté préfectoral du 20 mars 2012 "
                "et est ainsi rédigée"
            )
        ]

        # Act
        actual = parse_operations(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    OperationSpec,
                    contents=[
                        "Un article numéroté 7.7.6.3. est ",
                        self.make_tag("b", contents=["inséré"]),
                        " à la suite de ",
                    ],
                    data=OperationData(
                        operation_type="add",
                        keyword="inséré",
                        direction="rtl",
                    ),
                ),
                (
                    "l' article 7.7.6.2. des prescriptions annexées à l' arrêté préfectoral "
                    "du 20 mars 2012 et est ainsi rédigée"
                ),
            ],
        )

    def test_insert_article_in_chapter(self):
        # Arrange
        elements = [
            (
                "Un article numéroté 12.4.1. intitulé Dispositions spécifiques a l'atelier "
                "est insérée dans le chapitre 12.4."
            )
        ]

        # Act
        actual = parse_operations(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    OperationSpec,
                    contents=[
                        (
                            "Un article numéroté 12.4.1. intitulé Dispositions spécifiques a "
                            "l'atelier est "
                        ),
                        self.make_tag("b", contents=["insérée"]),
                        " dans le ",
                    ],
                    data=OperationData(
                        operation_type="add",
                        keyword="insérée",
                        direction="rtl",
                    ),
                ),
                "chapitre 12.4.",
            ],
        )

    def test_insert_article(self):
        # Arrange
        elements = ["un article numéroté 11.4.5. est inséré et est ainsi rédigé :"]

        # Act
        actual = parse_operations(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    OperationSpec,
                    contents=[
                        "un article numéroté 11.4.5. est ",
                        self.make_tag("b", contents=["inséré"]),
                        " et est ainsi rédigé :",
                    ],
                    data=OperationData(
                        operation_type="add",
                        has_operand="true",
                        keyword="inséré",
                        direction="rtl",
                    ),
                ),
            ],
        )

    def test_insert_title_after_another(self):
        # Arrange
        elements = [
            "Un titre 15, intitulé Dispositions particulières - Fabrication de crème enzymatique "
            "est inséré après le titre 14"
        ]

        # Act
        actual = parse_operations(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    OperationSpec,
                    contents=[
                        (
                            "Un titre 15, intitulé Dispositions particulières - Fabrication de "
                            "crème enzymatique est "
                        ),
                        self.make_tag("b", contents=["inséré"]),
                        " après le titre 14",
                    ],
                    data=OperationData(
                        operation_type="add",
                        has_operand="true",
                        keyword="inséré",
                        direction="rtl",
                    ),
                ),
            ],
        )


class TestDeleteOperations(BaseTestCaseHtml):
    def test_delete_abroge(self):
        # Arrange
        elements = [
            "Le dernier alinéa de l' article 1 .2 .2 de l'arrêté préfectoral précité est abrogé."
        ]

        # Act
        actual = parse_operations(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    OperationSpec,
                    contents=[
                        (
                            "Le dernier alinéa de l' article 1 .2 .2 de l'arrêté préfectoral "
                            "précité est "
                        ),
                        self.make_tag("b", contents=["abrogé"]),
                    ],
                    data=OperationData(
                        operation_type="delete",
                        keyword="abrogé",
                        direction="rtl",
                    ),
                ),
                ".",
            ],
        )

    def test_delete_supprime(self):
        # Arrange
        elements = [
            "L' article 11.1.2 relatif à la dérivation du bassin d'orage n° 1 vers le n° 2 "
            "est supprimé"
        ]

        # Act
        actual = parse_operations(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    OperationSpec,
                    contents=[
                        (
                            "L' article 11.1.2 relatif à la dérivation du bassin d'orage n° 1 "
                            "vers le n° 2 est "
                        ),
                        self.make_tag("b", contents=["supprimé"]),
                    ],
                    data=OperationData(
                        operation_type="delete",
                        keyword="supprimé",
                        direction="rtl",
                        has_operand=True,
                    ),
                ),
            ],
        )

    def test_delete_annule(self):
        # Arrange
        elements = [
            "L' article 2.13  Arrêté type  des prescriptions annexées à l' arrêté préfectoral "
            "modifié du 15 février 2005 est annulé."
        ]

        # Act
        actual = parse_operations(self.context, elements)

        # Assert
        assert_element_lists_equal(
            actual,
            [
                self.make_semantic_tag(
                    OperationSpec,
                    contents=[
                        (
                            "L' article 2.13  Arrêté type  des prescriptions annexées à l' arrêté "
                            "préfectoral modifié du 15 février 2005 est "
                        ),
                        self.make_tag("b", contents=["annulé"]),
                    ],
                    data=OperationData(
                        operation_type="delete",
                        keyword="annulé",
                        direction="rtl",
                    ),
                ),
                ".",
            ],
        )
