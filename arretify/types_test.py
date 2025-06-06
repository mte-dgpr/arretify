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
from unittest import mock

from bs4 import BeautifulSoup

from arretify._vendor.clients_api_droit.clients_api_droit.legifrance import LegifranceClient
from arretify._vendor.clients_api_droit.clients_api_droit.eurlex import EurlexClient
from arretify.settings import Settings
from .types import ParsingContext, SessionContext


class TestParsingContext(unittest.TestCase):
    def test_parsing_context_initialization(self):
        # Arrange
        legifrance_client = mock.Mock(spec=LegifranceClient)
        eurlex_client = mock.Mock(spec=EurlexClient)
        settings = mock.Mock(spec=Settings)
        soup = BeautifulSoup("<html></html>", "html.parser")
        lines = [
            {"start": (0, 0), "end": (0, 5), "contents": "Hello"},
            {"start": (1, 0), "end": (1, 5), "contents": "World"},
        ]
        session_context = SessionContext(
            settings=settings,
            legifrance_client=legifrance_client,
            eurlex_client=eurlex_client,
        )

        # Act
        parsing_context = ParsingContext.from_session_context(
            session_context, lines=lines, soup=soup
        )

        # Assert
        assert parsing_context.lines is lines
        assert parsing_context.soup is soup
        assert parsing_context.legifrance_client is legifrance_client
        assert parsing_context.eurlex_client is eurlex_client
        assert parsing_context.settings is settings
