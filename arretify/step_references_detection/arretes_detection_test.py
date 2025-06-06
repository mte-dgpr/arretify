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
    normalized_html_str,
)
from .arretes_detection import parse_arretes_references


process_children = make_testing_function_for_children_list(parse_arretes_references)


class TestParseArreteReferences(unittest.TestCase):

    def test_arrete_date1(self):
        assert process_children("Vu l'arrêté ministériel du 2 février 1998,") == [
            "Vu l'",
            normalized_html_str(
                """
                <a
                    class="dsr-document_reference"
                    data-is_resolvable="false"
                    data-uri="dsr://arrete-ministeriel___1998-02-02_"
                >
                    arrêté ministériel du
                    <time class="dsr-date" datetime="1998-02-02">
                        2 février 1998
                    </time>
                </a>
            """
            ),
            ",",
        ]

    def test_arrete_date1_end_modifiant(self):
        assert process_children(
            (
                "arrêté ministériel du 23 mai 2016 modifiant relatif aux installations "
                "de production de chaleur"
            )
        ) == [
            normalized_html_str(
                """
                <a
                    class="dsr-document_reference"
                    data-is_resolvable="false"
                    data-uri="dsr://arrete-ministeriel___2016-05-23_"
                >
                    arrêté ministériel du
                    <time class="dsr-date" datetime="2016-05-23">23 mai 2016</time>
                    modifiant
                </a>
            """
            ),
            " relatif aux installations de production de chaleur",
        ]

    def test_arrete_unknown(self):
        assert process_children("Vu l'arrêté du 2 février 1998,") == [
            "Vu l'",
            normalized_html_str(
                """
                <a
                    class="dsr-document_reference"
                    data-is_resolvable="false"
                    data-uri="dsr://arrete___1998-02-02_"
                >
                    arrêté du
                    <time class="dsr-date" datetime="1998-02-02">
                        2 février 1998
                    </time>
                </a>
            """
            ),
            ",",
        ]


class TestParseArretePluralReferences(unittest.TestCase):

    def test_references_multiple(self):
        assert process_children(
            "Les arrêtés préfectoraux n° 5213 du 28 octobre 1988 et n° 1636 du 24/03/95 blabla."
        ) == [
            "Les ",
            "arrêtés préfectoraux ",
            normalized_html_str(
                """
                <a
                    class="dsr-document_reference"
                    data-is_resolvable="false"
                    data-uri="dsr://arrete-prefectoral__5213_1988-10-28_"
                >
                    n° 5213 du
                    <time class="dsr-date" datetime="1988-10-28">
                        28 octobre 1988
                    </time>
                </a>
            """
            ),
            " et ",
            normalized_html_str(
                """
                <a
                    class="dsr-document_reference"
                    data-is_resolvable="false"
                    data-uri="dsr://arrete-prefectoral__1636_1995-03-24_"
                >
                    n° 1636 du
                    <time class="dsr-date" datetime="1995-03-24">
                        24/03/95
                    </time>
                </a>
            """
            ),
            " blabla.",
        ]


class TestParseArreteReferencesAll(unittest.TestCase):

    def test_several_references(self):
        assert process_children(
            (
                "Bla bla arrêté ministériel du 23 mai 2016 relatif aux installations de production "
                "de chaleur et arrêté préfectoral n° 1234-567/01."
            )
        ) == [
            "Bla bla ",
            normalized_html_str(
                """
                <a
                    class="dsr-document_reference"
                    data-is_resolvable="false"
                    data-uri="dsr://arrete-ministeriel___2016-05-23_"
                >
                    arrêté ministériel du
                    <time class="dsr-date" datetime="2016-05-23">
                        23 mai 2016
                    </time>
                </a>
            """
            ),
            " relatif aux installations de production de chaleur et ",
            normalized_html_str(
                """
                <a
                    class="dsr-document_reference"
                    data-is_resolvable="false"
                    data-uri="dsr://arrete-prefectoral__1234-567%2F01.__"
                >
                    arrêté préfectoral n° 1234-567/01.
                </a>
            """
            ),
        ]
