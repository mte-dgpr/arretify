import unittest

from bs4 import BeautifulSoup, Tag

from bench_convertisseur_xml.utils.testing import make_testing_function_for_single_tag
from .arretes_resolution import resolve_arrete_ministeriel_legifrance_id


process_arrete_document_reference = make_testing_function_for_single_tag(resolve_arrete_ministeriel_legifrance_id)


class TestResolveArreteMinisterielLegifranceId(unittest.TestCase):
    def test_resolve_simple(self):
        assert process_arrete_document_reference(
            '<a class="dsr-document_reference" data-is_resolvable="false" data-uri="dsr://arrete-ministeriel___1998-02-02_">arrêté ministériel du <time class="dsr-date" datetime="1998-02-02">2 février 1998</time></a>'
            ' relatif aux prélèvements et à la consommation d\'eau ainsi qu\'aux émissions de toute nature des installations classées pour la protection de l\'environnement soumises à autorisation', 
            css_selector='.dsr-document_reference'
        ) == (
            '<a class="dsr-document_reference" data-is_resolvable="true" data-uri="dsr://arrete-ministeriel_JORFTEXT000000204891__1998-02-02_" href="https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000000204891">'
            'arrêté ministériel du <time class="dsr-date" datetime="1998-02-02">2 février 1998</time></a>'
        )