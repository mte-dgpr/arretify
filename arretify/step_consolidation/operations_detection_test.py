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

from arretify.utils.testing import (
    make_testing_function_for_children_list,
)
from arretify.utils.testing import normalized_html_str
from .operations_detection import parse_operations

process_operations = make_testing_function_for_children_list(parse_operations)


class TestParseOperations(unittest.TestCase):
    def test_simple(self):
        assert process_operations("sont remplacées par celles définies par le présent arrêté.") == [
            normalized_html_str(
                """
                <span
                    class="dsr-operation"
                    data-direction="rtl"
                    data-has_operand="false"
                    data-keyword="remplacées"
                    data-operand=""
                    data-operation_type="replace"
                    data-references=""
                >
                    sont <b>remplacées</b>
                </span>
                """
            ),
            " par celles définies par le présent arrêté.",
        ]

    def test_has_operand(self):
        assert process_operations("sont remplacées comme suit :") == [
            normalized_html_str(
                """
                <span
                    class="dsr-operation"
                    data-direction="rtl"
                    data-has_operand="true"
                    data-keyword="remplacées"
                    data-operand=""
                    data-operation_type="replace"
                    data-references=""
                >
                    sont <b>remplacées</b> comme suit :
                </span>
                """
            ),
        ]

    def test_insert_operation(self):
        assert process_operations("Sont insérés après le") == [
            normalized_html_str(
                """
                <span
                    class="dsr-operation"
                    data-direction="rtl"
                    data-has_operand="true"
                    data-keyword="insérés"
                    data-operand=""
                    data-operation_type="add"
                    data-references=""
                >
                    Sont <b>insérés</b> après le
                </span>
                """
            ),
        ]

    def test_modification_operation(self):
        assert process_operations("susvisé sont ainsi modifiées :") == [
            normalized_html_str(
                """
                <span
                    class="dsr-operation"
                    data-direction="rtl"
                    data-has_operand="true"
                    data-keyword="modifiées"
                    data-operand=""
                    data-operation_type="replace"
                    data-references=""
                >
                    susvisé sont ainsi <b>modifiées</b> :
                </span>
                """
            ),
        ]

    def test_add_completed_as_follows(self):
        assert process_operations(
            "Le paragraphe 4.14 - Postes de chargement -déchargement est complété comme suit :"
        ) == [
            normalized_html_str(
                """
                <span
                    class="dsr-operation"
                    data-direction="rtl"
                    data-has_operand="true"
                    data-keyword="complété comme suit "
                    data-operand=""
                    data-operation_type="add"
                    data-references=""
                >
                    Le paragraphe 4.14 - Postes de chargement -déchargement est
                      <b>complété comme suit</b> :
                </span>
                """
            )
        ]

    def test_add_completed(self):
        assert process_operations(
            "Le paragraphe 4.19.1 - Réseau d'eau incendie est complété ainsi"
        ) == [
            normalized_html_str(
                """
                <span
                    class="dsr-operation"
                    data-direction="rtl"
                    data-has_operand="false"
                    data-keyword="complété ainsi"
                    data-operand=""
                    data-operation_type="add"
                    data-references=""
                >
                    Le paragraphe 4.19.1 - Réseau d'eau incendie est <b>complété ainsi</b>
                </span>
                """
            )
        ]

    def test_replace_operation(self):
        assert process_operations("Blabla. Il est remplacé par :") == [
            normalized_html_str(
                """
                <span
                    class="dsr-operation"
                    data-direction="rtl"
                    data-has_operand="true"
                    data-keyword="remplacé"
                    data-operand=""
                    data-operation_type="replace"
                    data-references=""
                >
                    Blabla. Il est <b>remplacé</b> par :
                </span>
                """
            ),
        ]

    def test_add_operation(self):
        assert process_operations(
            "Il est créé un article 4.3.14 à l'arrêté préfectoral du 10 décembre 2008"
        ) == [
            normalized_html_str(
                """
                <span
                    class="dsr-operation"
                    data-direction="rtl"
                    data-has_operand="false"
                    data-keyword="créé"
                    data-operand=""
                    data-operation_type="add"
                    data-references=""
                >
                    Il est <b>créé</b>
                </span>
                """
            ),
            " un article 4.3.14 à l'arrêté préfectoral du 10 décembre 2008",
        ]

    def test_add_operation_(self):
        assert process_operations(
            "Paragraphe 4.25 -Cuyes de stockages de TDI/MOI. Il est ajouté un paragraphe "
            "rédigé ainsi:"
        ) == [
            normalized_html_str(
                """
                <span
                    class="dsr-operation"
                    data-direction="rtl"
                    data-has_operand="true"
                    data-keyword="ajouté un paragraphe rédigé ainsi"
                    data-operand=""
                    data-operation_type="add"
                    data-references=""
                >
                    Paragraphe 4.25 -Cuyes de stockages de TDI/MOI. Il est
                    <b>ajouté un paragraphe rédigé ainsi</b>:
                </span>
                """
            )
        ]

    def test_add_operation_with_article_references(self):
        assert process_operations("L' article 8 .6 suivant est ajouté à l'arrêté préfectoral") == [
            normalized_html_str(
                """
                <span
                    class="dsr-operation"
                    data-direction="rtl"
                    data-has_operand="true"
                    data-keyword="ajouté"
                    data-operand=""
                    data-operation_type="add"
                    data-references=""
                >
                    L' article 8 .6 suivant est <b>ajouté</b> à l'arrêté préfectoral
                </span>
                """
            )
        ]

    def test_modified_by_addition_operation(self):
        assert process_operations(
            "Le chapitre 6.7 relatif aux déchets produits par l'établissement de l'arrêté "
            "préfectoral d'autorisation du 08 décembre 2009 est modifié par l'ajout du paragraphe"
        ) == [
            normalized_html_str(
                """
                <span
                    class="dsr-operation"
                    data-direction="rtl"
                    data-has_operand="true"
                    data-keyword="modifié par l'ajout"
                    data-operand=""
                    data-operation_type="add"
                    data-references=""
                >
                    Le chapitre 6.7 relatif aux déchets produits par l'établissement de l'arrêté
                    préfectoral d'autorisation du 08 décembre 2009 est <b>modifié par l'ajout</b>
                    du paragraphe
                </span>
                """
            )
        ]

    def test_replace_substituted(self):
        assert process_operations(
            "Le deuxième alinéa de l'article 4.3.8 de l'arrêté préfectoral précité est supprimé. "
            "Il est substitué par les alinéas suivants :"
        ) == [
            normalized_html_str(
                """
                <span
                    class="dsr-operation"
                    data-direction="rtl"
                    data-has_operand="true"
                    data-keyword="substitué"
                    data-operand=""
                    data-operation_type="replace"
                    data-references=""
                >
                    Le deuxième alinéa de l'article 4.3.8 de l'arrêté préfectoral précité
                    est supprimé. Il est <b>substitué</b> par les alinéas suivants :
                </span>
                """
            )
        ]

    def test_delete_abroge(self):
        assert process_operations(
            "Le dernier alinéa de l' article 1 .2 .2 de l'arrêté préfectoral précité est abrogé."
        ) == [
            normalized_html_str(
                """
                <span
                    class="dsr-operation"
                    data-direction="rtl"
                    data-has_operand="false"
                    data-keyword="abrogé"
                    data-operand=""
                    data-operation_type="delete"
                    data-references=""
                >
                    Le dernier alinéa de l' article 1 .2 .2 de l'arrêté préfectoral précité
                    est <b>abrogé</b>
                </span>
                """
            ),
            ".",
        ]

    def test_delete_supprime(self):
        assert process_operations(
            "L' article 11.1.2 relatif à la dérivation du bassin d'orage n° 1 vers le n° 2 "
            "est supprimé"
        ) == [
            normalized_html_str(
                """
                <span
                    class="dsr-operation"
                    data-direction="rtl"
                    data-has_operand="false"
                    data-keyword="supprimé"
                    data-operand=""
                    data-operation_type="delete"
                    data-references=""
                >
                    L' article 11.1.2 relatif à la dérivation du bassin d'orage n° 1 vers le n° 2
                    est <b>supprimé</b>
                </span>
                """
            )
        ]

    def test_delete_annule(self):
        assert process_operations(
            "L' article 2.13  Arrêté type  des prescriptions annexées à l' arrêté préfectoral "
            "modifié du 15 février 2005 est annulé."
        ) == [
            normalized_html_str(
                """
                <span
                    class="dsr-operation"
                    data-direction="rtl"
                    data-has_operand="false"
                    data-keyword="annulé"
                    data-operand=""
                    data-operation_type="delete"
                    data-references=""
                >
                    L' article 2.13  Arrêté type  des prescriptions annexées à l' arrêté préfectoral
                    modifié du 15 février 2005 est <b>annulé</b>
                </span>
                """
            ),
            ".",
        ]

    def test_canceled_and_replaced(self):
        assert process_operations(
            "Les prescriptions suivantes sont annulées et remplacées par les dispositions du "
            "présent arrêté :"
        ) == [
            normalized_html_str(
                """
                <span
                    class="dsr-operation"
                    data-direction="rtl"
                    data-has_operand="true"
                    data-keyword="annulées et remplacées"
                    data-operand=""
                    data-operation_type="replace"
                    data-references=""
                >
                    Les prescriptions suivantes sont <b>annulées et remplacées</b> par
                    les dispositions du présent arrêté :
                </span>
                """
            )
        ]

    def test_revoked_and_replaced(self):
        assert process_operations(
            "Les prescriptions de cet article sont abrogées et remplacées par celles ci-après :"
        ) == [
            normalized_html_str(
                """
                <span
                    class="dsr-operation"
                    data-direction="rtl"
                    data-has_operand="true"
                    data-keyword="abrogées et remplacées"
                    data-operand=""
                    data-operation_type="replace"
                    data-references=""
                >
                    Les prescriptions de cet article sont <b>abrogées et remplacées</b> par celles
                    ci-après :
                </span>
                """
            )
        ]

    def test_deleted_and_replaced(self):
        assert process_operations(
            "L' article 1 .2 .2 SITUATION DE L'ÉTABLISSEMENT est supprimé et remplacé par :"
        ) == [
            normalized_html_str(
                """
                <span
                    class="dsr-operation"
                    data-direction="rtl"
                    data-has_operand="true"
                    data-keyword="supprimé et remplacé"
                    data-operand=""
                    data-operation_type="replace"
                    data-references=""
                >
                    L' article 1 .2 .2 SITUATION DE L'ÉTABLISSEMENT est <b>supprimé et remplacé</b>
                    par :
                </span>
                """
            )
        ]

    def test_modified_and_replaced(self):
        assert process_operations(
            "2 .4 .2 L' article 15 .2 de l' arrêté préfectoral du 19 mars 2003 "
            "est modifié et remplacé par les dispositions suivantes :"
        ) == [
            normalized_html_str(
                """
                <span
                    class="dsr-operation"
                    data-direction="rtl"
                    data-has_operand="true"
                    data-keyword="modifié et remplacé"
                    data-operand=""
                    data-operation_type="replace"
                    data-references=""
                >
                    2 .4 .2 L' article 15 .2 de l' arrêté préfectoral du 19 mars 2003 est
                      <b>modifié et remplacé</b> par les dispositions suivantes :
                </span>
                """
            )
        ]

    # Détection " Sont insérés après le"
    def test_insert_operation(self):
        assert process_operations("Sont insérés après le") == [
            normalized_html_str(
                """
                <span
                    class="dsr-operation"
                    data-direction="rtl"
                    data-has_operand="true"
                    data-keyword="insérés"
                    data-operand=""
                    data-operation_type="add"
                    data-references=""
                >
                    Sont <b>insérés</b> après le
                </span>
                """
            ),
        ]

    # Détection "complété comme suit :"
    def test_add_completed_as_follows(self):
        assert process_operations("est complété comme suit :") == [
            normalized_html_str(
                """
                <span
                    class="dsr-operation"
                    data-direction="rtl"
                    data-has_operand="true"
                    data-keyword="complété comme suit "
                    data-operand=""
                    data-operation_type="add"
                    data-references=""
                >
                    est <b>complété comme suit</b> :
                </span>
                """
            ),
        ]

    # Détection de l'opération malgré la présence du point
    def test_replace_operation(self):
        assert process_operations("Il est remplacé par :") == [
            normalized_html_str(
                """
                <span
                    class="dsr-operation"
                    data-direction="rtl"
                    data-has_operand="true"
                    data-keyword="remplacé"
                    data-operand=""
                    data-operation_type="replace"
                    data-references=""
                >
                    Il est <b>remplacé</b> par :
                </span>
                """
            ),
        ]
