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

from arretify.utils.testing import make_testing_function_for_single_tag, normalized_html_str

from .arretes_resolution import resolve_arrete_ministeriel_legifrance_id

process_arrete_document_reference = make_testing_function_for_single_tag(
    resolve_arrete_ministeriel_legifrance_id
)


class TestResolveArreteMinisterielLegifranceId(unittest.TestCase):
    def test_resolve_simple(self):
        assert (
            process_arrete_document_reference(
                """
                <a
                    data-spec="document_reference"
                    data-date="1998-02-02"
                    data-type="arrete-ministeriel"
                >
                    arrêté ministériel du
                    <time data-spec="date" datetime="1998-02-02">
                        2 février 1998
                    </time>
                </a>
                relatif aux prélèvements et à la consommation d'eau ainsi
                qu'aux émissions de toute nature des installations classées
                pour la protection de l'environnement soumises à autorisation
            """,
                css_selector="[data-spec='document_reference']",
            )
            == normalized_html_str(
                """
            <a
                data-spec="document_reference"
                data-date="1998-02-02"
                data-id="JORFTEXT000000204891"
                data-type="arrete-ministeriel"
                href="https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000000204891"
            >
                arrêté ministériel du
                <time data-spec="date" datetime="1998-02-02">
                    2 février 1998
                </time>
            </a>
        """
            )
        )
