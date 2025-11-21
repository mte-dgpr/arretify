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

from arretify.utils.testing import make_testing_function_for_children_list, normalized_html_str

from .operations_detection import parse_operations

process_operations = make_testing_function_for_children_list(parse_operations)


class TestReplaceOperations(unittest.TestCase):
    def test_has_operand(self):
        assert process_operations("sont remplacées comme suit :") == [
            normalized_html_str(
                """
                <span
                    data-direction="rtl"
                    data-has_operand="true"
                    data-keyword="remplacées"
                    data-operation_type="replace"
                    data-spec="operation"
                >
                    sont <b>remplacées</b> comme suit :
                </span>
                """
            ),
        ]

    def test_replace_substituted(self):
        assert process_operations(
            "Le deuxième alinéa de l'article 4.3.8 de l'arrêté préfectoral précité est supprimé. "
            "Il est substitué par les alinéas suivants :"
        ) == [
            normalized_html_str(
                """
                <span
                    data-direction="rtl"
                    data-has_operand="true"
                    data-keyword="substitué"
                    data-operation_type="replace"
                    data-spec="operation"
                >
                    Le deuxième alinéa de l'article 4.3.8 de l'arrêté préfectoral précité
                    est supprimé. Il est <b>substitué</b> par les alinéas suivants :
                </span>
                """
            )
        ]

    def test_canceled_and_replaced(self):
        assert process_operations(
            "Les prescriptions suivantes sont annulées et remplacées par les dispositions du "
            "présent arrêté :"
        ) == [
            normalized_html_str(
                """
                <span
                    data-direction="rtl"
                    data-has_operand="true"
                    data-keyword="annulées et remplacées"
                    data-operation_type="replace"
                    data-spec="operation"
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
                    data-direction="rtl"
                    data-has_operand="true"
                    data-keyword="abrogées et remplacées"
                    data-operation_type="replace"
                    data-spec="operation"
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
                    data-direction="rtl"
                    data-has_operand="true"
                    data-keyword="supprimé et remplacé"
                    data-operation_type="replace"
                    data-spec="operation"
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
                    data-direction="rtl"
                    data-has_operand="true"
                    data-keyword="modifié et remplacé"
                    data-operation_type="replace"
                    data-spec="operation"
                >
                    2 .4 .2 L' article 15 .2 de l' arrêté préfectoral du 19 mars 2003 est
                    <b>modifié et remplacé</b> par les dispositions suivantes :
                </span>
                """
            )
        ]

    def test_modified_and_completed_by(self):
        assert process_operations(
            "L'article 5 des prescriptions techniques annexées à l'arrêté préfectoral du"
            " 11 juin 2004 est modifié et complété par les dispositions suivantes :"
        ) == [
            normalized_html_str(
                """
                <span
                    data-direction="rtl"
                    data-has_operand="true"
                    data-keyword="modifié et complété"
                    data-operation_type="replace"
                    data-spec="operation"
                >
                    L'article 5 des prescriptions techniques annexées à l'arrêté préfectoral du
                    11 juin 2004 est <b>modifié et complété</b> par les dispositions suivantes :
                </span>
                """
            )
        ]

    def test_modified_completed_or_annulled(self):
        assert process_operations(
            "Les dispositions de l'arrêté préfectoral n09-0150 du 20 janvier 2009 susvisé"
            " sont modifiées, complétées, ou annulées par les dispositions fixées aux articles"
            " suivants, et dont le récapitulatif figure ci-après :"
        ) == [
            normalized_html_str(
                """
                <span
                    data-direction="rtl"
                    data-has_operand="true"
                    data-keyword="modifiées, complétées, ou annulées"
                    data-operation_type="replace"
                    data-spec="operation"
                >
                    Les dispositions de l'arrêté préfectoral n09-0150 du 20 janvier 2009 susvisé
                    sont <b>modifiées, complétées, ou annulées</b> par les dispositions fixées
                    aux articles suivants, et dont le récapitulatif figure ci-après :
                </span>
                """
            )
        ]

    def test_modified_simple_disposition(self):
        assert process_operations(
            "La dernière phrase de l'article 8.1.1.2 de l'arrêté préfectoral du 10 décembre 2008"
            " est remplacée par la disposition suivante :"
        ) == [
            normalized_html_str(
                """
                <span
                    data-direction="rtl"
                    data-has_operand="true"
                    data-keyword="remplacée"
                    data-operation_type="replace"
                    data-spec="operation"
                >
                    La dernière phrase de l'article 8.1.1.2 de l'arrêté préfectoral du 10 décembre
                    2008 est <b>remplacée</b> par la disposition suivante :
                </span>
                """
            )
        ]

    def test_modified_operand(self):
        assert process_operations(
            "La dernière phrase de l'article 8.1.1.2 de l'arrêté préfectoral du 10 décembre 2008"
            " est ainsi modifiée :"
        ) == [
            normalized_html_str(
                """
                <span
                    data-direction="rtl"
                    data-has_operand="true"
                    data-keyword="modifiée"
                    data-operation_type="replace"
                    data-spec="operation"
                >
                    La dernière phrase de l'article 8.1.1.2 de l'arrêté préfectoral du 10 décembre
                    2008 est ainsi <b>modifiée</b> :
                </span>
                """
            )
        ]

    def test_delete_replace_plural(self):
        assert process_operations(
            "Les dispositions de l'article 2.8 - Arrêtés types sont supprimées et sont remplacées"
            " par celles du tableau suivant :"
        ) == [
            normalized_html_str(
                """
                <span
                    data-direction="rtl"
                    data-has_operand="true"
                    data-keyword="supprimées et sont remplacées"
                    data-operation_type="replace"
                    data-spec="operation"
                >
                    Les dispositions de l'article 2.8 - Arrêtés types sont <b>supprimées et sont
                    remplacées</b> par celles du tableau suivant :
                </span>
                """
            )
        ]

    def test_update(self):
        assert process_operations(
            "Le tableau de l'article 1.2.1 de l'arrêté préfectoral du 10 décembre 2008 "
            "est mis à jour de la façon suivante :"
        ) == [
            normalized_html_str(
                """
                <span
                    data-direction="rtl"
                    data-has_operand="true"
                    data-keyword="mis à jour"
                    data-operation_type="replace"
                    data-spec="operation"
                >
                    Le tableau de l'article 1.2.1 de l'arrêté préfectoral du 10 décembre 2008
                    est <b>mis à jour</b> de la façon suivante :
                </span>
                """
            )
        ]


class TestAddOperations(unittest.TestCase):
    def test_add_completed_as_follows(self):
        assert process_operations(
            "Le paragraphe 4.14 - Postes de chargement -déchargement est complété comme suit :"
        ) == [
            normalized_html_str(
                """
                <span
                    data-direction="rtl"
                    data-has_operand="true"
                    data-keyword="complété"
                    data-operation_type="add"
                    data-spec="operation"
                >
                    Le paragraphe 4.14 - Postes de chargement -déchargement est
                    <b>complété</b> comme suit :
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
                    data-direction="rtl"
                    data-keyword="complété"
                    data-operation_type="add"
                    data-spec="operation"
                >
                    Le paragraphe 4.19.1 - Réseau d'eau incendie est <b>complété</b> ainsi
                </span>
                """
            )
        ]

    def test_completed_d_multiple_articles(self):
        assert process_operations(
            "Les prescriptions de l' article 8.3. dispositions spécifiques à l'installation de "
            "combustion de l' arrêté préfectoral du 15 mars 2013 sont complétés d' articles 8.3 .8 "
            "et 8.3 .9 ainsi rédigés :"
        ) == [
            normalized_html_str(
                """
                <span
                    data-direction="rtl"
                    data-keyword="complétés"
                    data-operation_type="add"
                    data-spec="operation"
                >
                    Les prescriptions de l' article 8.3. dispositions spécifiques à l'installation
                    de combustion de l' arrêté préfectoral du 15 mars 2013 sont <b>complétés</b> d'
                </span>
                """
            ),
            " articles 8.3 .8 et 8.3 .9 ainsi rédigés :",
        ]

    def test_add_operation(self):
        assert process_operations(
            "Il est créé un article 4.3.14 à l'arrêté préfectoral du 10 décembre 2008"
        ) == [
            normalized_html_str(
                """
                <span
                    data-direction="rtl"
                    data-keyword="créé"
                    data-operation_type="add"
                    data-spec="operation"
                >
                    Il est <b>créé</b> un
                </span>
                """
            ),
            "article 4.3.14 à l'arrêté préfectoral du 10 décembre 2008",
        ]

    def test_created_article_end(self):
        assert process_operations(
            "Un article additionnel 8.2.5 relatif au fonctionnement du casier VIII en mode "
            "bioréacteur est créé en fin de chapitre 8.2 intitulé Zone de stockage de déchets non"
            "dangereux de l' arrêté préfectoral du 28 novembre 2017"
        ) == [
            normalized_html_str(
                """
                <span
                    data-direction="rtl"
                    data-keyword="créé"
                    data-operation_type="add"
                    data-spec="operation"
                >
                    Un article additionnel 8.2.5 relatif au fonctionnement du casier VIII en mode
                    bioréacteur est <b>créé</b> en fin de
                </span>
                """
            ),
            "chapitre 8.2 intitulé Zone de stockage de déchets nondangereux de l' "
            "arrêté préfectoral du 28 novembre 2017",
        ]

    def test_created_new_chapter(self):
        assert process_operations(
            "Il est créé un nouveau chapitre 11.6 à l' arrêté du 16 juillet 2010 rédigé"
            " comme suit :"
        ) == [
            normalized_html_str(
                """
                <span
                    data-direction="rtl"
                    data-keyword="créé"
                    data-operation_type="add"
                    data-spec="operation"
                >
                    Il est <b>créé</b> un nouveau
                </span>
                """
            ),
            "chapitre 11.6 à l' arrêté du 16 juillet 2010 rédigé comme suit :",
        ]

    def test_created_new_article(self):
        assert process_operations(
            "Il est créé un nouvel article 8.2.3 à l' arrêté du 16 juillet 2010 rédigé comme suit :"
        ) == [
            normalized_html_str(
                """
                <span
                    data-direction="rtl"
                    data-keyword="créé"
                    data-operation_type="add"
                    data-spec="operation"
                >
                    Il est <b>créé</b> un nouvel
                </span>
                """
            ),
            "article 8.2.3 à l' arrêté du 16 juillet 2010 rédigé comme suit :",
        ]

    def test_created_two_new_articles(self):
        assert process_operations(
            "Sous le tableau de la liste des activités autorisées, il est créé deux nouveaux"
            " articles ainsi rédigés :"
        ) == [
            normalized_html_str(
                """
                <span
                    data-direction="rtl"
                    data-has_operand="true"
                    data-keyword="créé"
                    data-operation_type="add"
                    data-spec="operation"
                >
                    Sous le tableau de la liste des activités autorisées,
                    il est <b>créé</b> deux nouveaux articles ainsi rédigés :
                </span>
                """
            )
        ]

    def test_add_operation_(self):
        assert process_operations(
            "Paragraphe 4.25 -Cuyes de stockages de TDI/MOI. Il est ajouté un paragraphe "
            "rédigé ainsi:"
        ) == [
            normalized_html_str(
                """
                <span
                    data-direction="rtl"
                    data-has_operand="true"
                    data-keyword="ajouté"
                    data-operation_type="add"
                    data-spec="operation"
                >
                    Paragraphe 4.25 -Cuyes de stockages de TDI/MOI. Il est
                    <b>ajouté</b> un paragraphe rédigé ainsi:
                </span>
                """
            )
        ]

    def test_add_operation_with_article_references(self):
        assert process_operations("L' article 8 .6 suivant est ajouté à l'arrêté préfectoral") == [
            normalized_html_str(
                """
                <span
                    data-direction="rtl"
                    data-has_operand="true"
                    data-keyword="ajouté"
                    data-operation_type="add"
                    data-spec="operation"
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
                    data-direction="rtl"
                    data-has_operand="true"
                    data-keyword="modifié par l'ajout"
                    data-operation_type="add"
                    data-spec="operation"
                >
                    Le chapitre 6.7 relatif aux déchets produits par l'établissement de l'arrêté
                    préfectoral d'autorisation du 08 décembre 2009 est <b>modifié par l'ajout</b>
                    du paragraphe
                </span>
                """
            )
        ]

    def test_insert_paragraph_at_start(self):
        assert process_operations(
            "2.4.3 Le paragraphe suivant est inséré au début de l' article 15.4"
        ) == [
            normalized_html_str(
                """
                <span
                    data-direction="rtl"
                    data-keyword="inséré"
                    data-operation_type="add"
                    data-spec="operation"
                >
                    2.4.3 Le paragraphe suivant est <b>inséré</b> au début de
                </span>
                """
            ),
            "l' article 15.4",
        ]

    def test_insert_after_alinea(self):
        assert process_operations(
            "A la suite du 1er  alinéa de l' article 14.5 de l' arrêté préfectoral du 18 avril 2005"
            " sont insérées les dispositions suivantes :"
        ) == [
            normalized_html_str(
                """
                <span
                    data-direction="rtl"
                    data-has_operand="true"
                    data-keyword="insérées"
                    data-operation_type="add"
                    data-spec="operation"
                >
                    A la suite du 1er  alinéa de l' article 14.5 de l' arrêté préfectoral
                    du 18 avril 2005 sont <b>insérées</b> les dispositions suivantes :
                </span>
                """
            )
        ]

    def test_insert_new_alinea_after(self):
        assert process_operations(
            "Après le 4ème alinéa de l'article 4.3.8 de l'arrêté préfectoral précité,"
            " il est inséré le nouvel alinéa suivant :"
        ) == [
            normalized_html_str(
                """
                <span
                    data-direction="rtl"
                    data-has_operand="true"
                    data-keyword="inséré"
                    data-operation_type="add"
                    data-spec="operation"
                >
                    Après le 4ème alinéa de l'article 4.3.8 de l'arrêté préfectoral précité,
                    il est <b>inséré</b> le nouvel alinéa suivant :
                </span>
                """
            )
        ]

    def test_insert_two_new_alinea(self):
        assert process_operations(
            "Après lé 6ème alinéa de l'article 4.3.8 de l'arrêté préfectoral précité,"
            " il est inséré les deux nouveaux alinéas suivants :"
        ) == [
            normalized_html_str(
                """
                <span
                    data-direction="rtl"
                    data-has_operand="true"
                    data-keyword="inséré"
                    data-operation_type="add"
                    data-spec="operation"
                >
                    Après lé 6ème alinéa de l'article 4.3.8 de l'arrêté préfectoral précité,
                    il est <b>inséré</b> les deux nouveaux alinéas suivants :
                </span>
                """
            )
        ]

    def test_insert_article_after(self):
        assert process_operations(
            "Un article numéroté 7.7.6.3. est inséré à la suite de l' article 7.7.6.2."
            " des prescriptions annexées à l' arrêté préfectoral du 20 mars 2012 et"
            " est ainsi rédigée"
        ) == [
            normalized_html_str(
                """
                <span
                    data-direction="rtl"
                    data-keyword="inséré"
                    data-operation_type="add"
                    data-spec="operation"
                >
                    Un article numéroté 7.7.6.3. est <b>inséré</b> à la suite de
                </span>
                """
            ),
            "l' article 7.7.6.2. des prescriptions annexées à l' arrêté préfectoral du "
            "20 mars 2012 et est ainsi rédigée",
        ]

    def test_insert_article_in_chapter(self):
        assert process_operations(
            "Un article numéroté 12.4.1. intitulé Dispositions spécifiques a l'atelier est insérée"
            " dans le chapitre 12.4."
        ) == [
            normalized_html_str(
                """
                <span
                    data-direction="rtl"
                    data-keyword="insérée"
                    data-operation_type="add"
                    data-spec="operation"
                >
                    Un article numéroté 12.4.1. intitulé Dispositions spécifiques a l'atelier est
                    <b>insérée</b> dans le
                </span>
                """
            ),
            "chapitre 12.4.",
        ]

    def test_insert_article(self):
        assert process_operations(
            "un article numéroté 11.4.5. est inséré et est ainsi rédigé :"
        ) == [
            normalized_html_str(
                """
                <span
                    data-direction="rtl"
                    data-has_operand="true"
                    data-keyword="inséré"
                    data-operation_type="add"
                    data-spec="operation"
                >
                    un article numéroté 11.4.5. est <b>inséré</b> et est ainsi rédigé :
                </span>
                """
            )
        ]

    def test_insert_title_after_another(self):
        assert process_operations(
            "Un titre 15, intitulé Dispositions particulières - Fabrication de crème enzymatique"
            " est inséré après le titre 14"
        ) == [
            normalized_html_str(
                """
                <span
                    data-direction="rtl"
                    data-has_operand="true"
                    data-keyword="inséré"
                    data-operation_type="add"
                    data-spec="operation"
                >
                    Un titre 15, intitulé Dispositions particulières - Fabrication de crème
                    enzymatique est <b>inséré</b> après le titre 14
                </span>
                """
            )
        ]


class TestDeleteOperations(unittest.TestCase):
    def test_delete_abroge(self):
        assert process_operations(
            "Le dernier alinéa de l' article 1 .2 .2 de l'arrêté préfectoral précité est abrogé."
        ) == [
            normalized_html_str(
                """
                <span
                    data-direction="rtl"
                    data-keyword="abrogé"
                    data-operation_type="delete"
                    data-spec="operation"
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
                    data-direction="rtl"
                    data-keyword="supprimé"
                    data-operation_type="delete"
                    data-spec="operation"
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
                    data-direction="rtl"
                    data-keyword="annulé"
                    data-operation_type="delete"
                    data-spec="operation"
                >
                    L' article 2.13  Arrêté type  des prescriptions annexées à l' arrêté préfectoral
                    modifié du 15 février 2005 est <b>annulé</b>
                </span>
                """
            ),
            ".",
        ]
