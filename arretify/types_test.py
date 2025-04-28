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
