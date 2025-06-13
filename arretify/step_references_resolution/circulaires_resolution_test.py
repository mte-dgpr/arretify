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
                data-date="1986-07-23"
                data-type="circulaire"
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
                data-date="1986-07-23"
                data-id="JORFTEXT000000866509"
                data-type="circulaire"
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
