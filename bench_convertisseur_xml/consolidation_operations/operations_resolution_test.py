import unittest

from bench_convertisseur_xml.utils.testing import create_bs, normalized_html_str
from bench_convertisseur_xml.utils import html
from .operations_resolution import resolve_references_and_operands


class TestParseOperations(unittest.TestCase):

    def setUp(self):
        html._ID_COUNTER = 0

    def test_several_references_no_operand(self):
        # Arrange
        soup = create_bs(
            normalized_html_str(
                """
            <div class="dsr-alinea">
                Les
                <span class="dsr-sections_and_document_references">
                    <span class="dsr-section_reference_multiple">
                        <a class="dsr-section_reference">
                            paragraphes 3
                        </a>
                        et
                        <a class="dsr-section_reference">
                            4 de l'article 8.5.1.1
                        </a>
                    </span>
                    de l'
                    <a class="dsr-document_reference">
                        arrêté préfectoral du
                        <time class="dsr-date" datetime="2008-12-10">
                            10 décembre 2008
                        </time>
                    </a>
                </span>
                <span class="dsr-operation" data-direction="rtl" data-has_operand="" data-keyword="supprimés" data-operand="" data-operation_type="delete">
                    sont
                    <b>
                        supprimés
                    </b>
                </span>
            </div>
        """  # noqa: E501
            )
        )

        # Act
        resolve_references_and_operands(soup.find(class_="dsr-operation"))

        # Assert
        # Check that element_id was added to both references, and that the references were
        # added to the operation
        assert str(soup) == normalized_html_str(
            """
            <div class="dsr-alinea">
                Les
                <span class="dsr-sections_and_document_references">
                    <span class="dsr-section_reference_multiple">
                        <a class="dsr-section_reference" data-element_id="1">
                            paragraphes 3
                        </a>
                        et
                        <a class="dsr-section_reference" data-element_id="2">
                            4 de l'article 8.5.1.1
                        </a>
                    </span>
                    de l'
                    <a class="dsr-document_reference">
                        arrêté préfectoral du
                        <time class="dsr-date" datetime="2008-12-10">
                            10 décembre 2008
                        </time>
                    </a>
                </span>
                <span class="dsr-operation" data-direction="rtl" data-has_operand="" data-keyword="supprimés" data-operand="" data-operation_type="delete" data-references="1,2">
                    sont
                    <b>
                        supprimés
                    </b>
                </span>
            </div>
        """  # noqa: E501
        )

    def test_one_reference_one_operand(self):
        # Arrange
        soup = create_bs(
            normalized_html_str(
                """
            <div class="dsr-alinea">
                La dernière phrase de l'
                <span class="dsr-sections_and_document_references">
                    <a class="dsr-section_reference">
                        article 8.1.1.2
                    </a>
                    de l'
                    <a class="dsr-document_reference">
                        arrêté préfectoral du
                        <time class="dsr-date" datetime="2008-12-10">
                                10 décembre 2008
                        </time>
                    </a>
                </span>
                <span class="dsr-operation" data-direction="rtl" data-has_operand="true" data-keyword="remplacée" data-operand="2" data-operation_type="replace">
                    est
                    <b>
                        remplacée
                    </b>
                    par la disposition suivante :
                </span>
                <q>
                    Un relevé hebdomadaire de chacun des compteurs d'eau est réalisé par l'exploitant
                </q>
                .
            </div>
        """  # noqa: E501
            )
        )

        # Act
        resolve_references_and_operands(soup.find(class_="dsr-operation"))

        # Assert
        assert str(soup) == normalized_html_str(
            """
            <div class="dsr-alinea">
                La dernière phrase de l'
                <span class="dsr-sections_and_document_references">
                    <a class="dsr-section_reference" data-element_id="1">
                        article 8.1.1.2
                    </a>
                    de l'
                    <a class="dsr-document_reference">
                        arrêté préfectoral du
                        <time class="dsr-date" datetime="2008-12-10">
                                10 décembre 2008
                        </time>
                    </a>
                </span>
                <span class="dsr-operation" data-direction="rtl" data-has_operand="true" data-keyword="remplacée" data-operand="2" data-operation_type="replace" data-references="1">
                    est
                    <b>
                        remplacée
                    </b>
                    par la disposition suivante :
                </span>
                <q data-element_id="2">
                    Un relevé hebdomadaire de chacun des compteurs d'eau est réalisé par l'exploitant
                </q>
                .
            </div>
        """  # noqa: E501
        )

    def test_with_single_document_reference(self):
        # Arrange
        soup = create_bs(
            normalized_html_str(
                """
            <div class="dsr-alinea">
                Les prescriptions de l'
                <a class="dsr-document_reference">
                    arrêté préfectoral du
                    <time class="dsr-date" datetime="2008-12-10">
                            10 décembre 2008
                    </time>
                </a>
                <span class="dsr-operation" data-direction="rtl" data-has_operand="" data-keyword="abrogées" data-operand="" data-operation_type="delete">
                    sont
                    <b>
                        abrogées
                    </b>
                    .
                </span>
            </div>
        """  # noqa: E501
            )
        )

        # Act
        resolve_references_and_operands(soup.find(class_="dsr-operation"))

        # Assert
        assert str(soup) == normalized_html_str(
            """
            <div class="dsr-alinea">
                Les prescriptions de l'
                <a class="dsr-document_reference" data-element_id="1">
                    arrêté préfectoral du
                    <time class="dsr-date" datetime="2008-12-10">
                            10 décembre 2008
                    </time>
                </a>
                <span class="dsr-operation" data-direction="rtl" data-has_operand="" data-keyword="abrogées" data-operand="" data-operation_type="delete" data-references="1">
                    sont
                    <b>
                        abrogées
                    </b>
                    .
                </span>
            </div>
        """  # noqa: E501
        )
