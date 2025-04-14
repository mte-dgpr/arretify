import unittest

from arretify.utils.testing import (
    make_testing_function_for_single_tag,
    normalized_html_str,
)
from .decrets_resolution import resolve_decret_legifrance_id

process_decret_document_reference = make_testing_function_for_single_tag(
    resolve_decret_legifrance_id
)


class TestResolveDecretLegifranceId(unittest.TestCase):
    def test_resolve_simple(self):
        assert (
            process_decret_document_reference(
                """
            <a
                class="dsr-document_reference"
                data-is_resolvable="false"
                data-uri="dsr://decret___2005-04-20_"
            >
                décret du
                <time class="dsr-date" datetime="2005-04-20">
                    20 avril 2005
                </time>
            </a>
            relatif au programme national d'action contre la pollution des milieux aquatiques
            par certaines substances dangereuses
            """,
                css_selector=".dsr-document_reference",
            )
            == normalized_html_str(
                """
            <a
                class="dsr-document_reference"
                data-is_resolvable="true"
                data-uri="dsr://decret_JORFTEXT000000259598__2005-04-20_"
                href="https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000000259598"
            >
                décret du
                <time class="dsr-date" datetime="2005-04-20">
                    20 avril 2005
                </time>
            </a>
            """
            )
        )
