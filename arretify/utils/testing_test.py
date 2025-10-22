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

from bs4.element import Tag

from .testing import normalized_html_str, normalized_soup


class TestHtmlNormalization(unittest.TestCase):

    def test_remove_all_spaces_and_newlines_except_after_inline(self):
        assert (
            normalized_html_str(
                """
                <div>
                    bla <a>link</a>
                    <span class="start">
                        blo <b>bold blo</b>
                    </span>
                </div>
                <div>
                    <div>
                        bli <i>italic bli</i>
                    </div>
                    <blockquote>
                        blu <u>underline blu</u>
                    </blockquote>
                </div>
                """
            )
            == (
                '<div>bla <a>link</a><span class="start">blo <b>bold blo</b></span></div>'
                "<div><div>bli <i>italic bli</i></div><blockquote>blu <u>underline blu</u>"
                "</blockquote></div>"
            )
        )

    def test_insert_space_between_string_and_inline(self):
        assert (
            normalized_html_str(
                """
                    arrêté ministériel du
                    <time data-spec="date" datetime="1998-02-02">
                        2 février 1998
                    </time>
                """
            )
            == (
                'arrêté ministériel du <time data-spec="date" datetime="1998-02-02">'
                "2 février 1998</time>"
            )
        )

    def test_insert_space_between_inline_and_string(self):
        assert (
            normalized_html_str(
                """
                    <time data-spec="date" datetime="1998-02-02">
                        2 février 1998
                    </time>
                    arrêté ministériel du
                """
            )
            == (
                '<time data-spec="date" datetime="1998-02-02">'
                "2 février 1998</time> arrêté ministériel du"
            )
        )

    def test_insert_space_between_string_lines(self):
        assert (
            normalized_html_str(
                """
                    <a>
                        bla
                    </a>
                    he ho
                    hi hu
                    ha hy ha
                """
            )
            == ("<a>bla</a> he ho hi hu ha hy ha")
        )

    def test_remove_empty_strings(self):
        bs = normalized_soup(
            """
            <div id="el1">
                <div id="el2"></div>
                <div id="el3"></div>
            </div>
            <div id="el4"></div>
            <div id="el5">
                <div id="el6">
                    <div id="el7"></div>
                </div>
            </div>
            """
        )
        assert str(bs) == (
            '<div id="el1"><div id="el2"></div><div id="el3"></div></div>'
            '<div id="el4"></div>'
            '<div id="el5"><div id="el6"><div id="el7"></div></div></div>'
        )
        assert all(isinstance(d, Tag) for d in bs.descendants)
