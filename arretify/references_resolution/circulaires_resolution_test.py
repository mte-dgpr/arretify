import unittest

from arretify.utils.testing import (
    make_testing_function_for_single_tag,
    normalized_html_str,
)
from .circulaires_resolution import resolve_circulaire_legifrance_id

process_circulaire_document_reference = make_testing_function_for_single_tag(
    resolve_circulaire_legifrance_id
)


class TestResolveCirculaireLegifranceId(unittest.TestCase):
    def test_resolve_simple(self):
        assert (
            process_circulaire_document_reference(
                """
            <a
                class="dsr-document_reference"
                data-is_resolvable="false"
                data-uri="dsr://circulaire___1986-07-23_"
            >
                Circulaire du
                <time class="dsr-date" datetime="1986-07-23">
                    23 juillet 1986
                </time>
            </a>
            relative aux vibrations mecaniques emises dans l'environnement par les
            installations classees pour la protection de l'environnement
            """,
                css_selector=".dsr-document_reference",
            )
            == normalized_html_str(
                """
            <a
                class="dsr-document_reference"
                data-is_resolvable="true"
                data-uri="dsr://circulaire_JORFTEXT000000866509__1986-07-23_"
                href="https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000000866509"
            >
                Circulaire du
                <time class="dsr-date" datetime="1986-07-23">
                    23 juillet 1986
                </time>
            </a>
            """
            )
        )
