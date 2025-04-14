import unittest

from .uri import render_uri, parse_uri, _validate_sections
from .types import DocumentType, Document, SectionType, Section


class TestRenderUri(unittest.TestCase):

    def test_simple_document_all_fields(self):
        uri = render_uri(
            Document(
                type=DocumentType.arrete_prefectoral,
                id="123",
                num="456",
                date="2022-01-01",
                title="Arrêté préfectoral 123 456",
            )
        )
        assert (
            uri
            == "dsr://arrete-prefectoral_123_456_2022-01-01_Arr%C3%AAt%C3%A9%20pr%C3%A9fectoral%20123%20456"  # noqa: E501
        )

    def test_missing_fields(self):
        uri = render_uri(
            Document(
                type=DocumentType.arrete_prefectoral,
                id=None,
                num=None,
                date=None,
                title=None,
            )
        )
        assert uri == "dsr://arrete-prefectoral____"

    def test_with_simple_section(self):
        uri = render_uri(
            Document(
                type=DocumentType.arrete_prefectoral,
                id="123",
                num="456",
                date="2022-01-01",
                title="Arrêté préfectoral 123 456",
            ),
            Section(
                type=SectionType.article,
                start_id="1",
                start_num="2",
                end_id="3",
                end_num="4",
            ),
        )
        assert (
            uri
            == "dsr://arrete-prefectoral_123_456_2022-01-01_Arr%C3%AAt%C3%A9%20pr%C3%A9fectoral%20123%20456/article_1_2_3_4"  # noqa: E501
        )

    def test_with_section_missing_attributes(self):
        uri = render_uri(
            Document(
                type=DocumentType.arrete_prefectoral,
                id="123",
                num="456",
                date="2022-01-01",
                title="Arrêté préfectoral 123 456",
            ),
            Section(
                type=SectionType.article,
                start_id="1",
            ),
        )
        assert (
            uri
            == "dsr://arrete-prefectoral_123_456_2022-01-01_Arr%C3%AAt%C3%A9%20pr%C3%A9fectoral%20123%20456/article_1___"  # noqa: E501
        )


class TestParseUri(unittest.TestCase):

    def test_simple_document_all_fields(self):
        document, sections = parse_uri(
            "dsr://arrete-prefectoral_123_456_2022-01-01_Arr%C3%AAt%C3%A9%20pr%C3%A9fectoral%20123%20456"  # noqa: E501
        )
        assert document == Document(
            type=DocumentType.arrete_prefectoral,
            id="123",
            num="456",
            date="2022-01-01",
            title="Arrêté préfectoral 123 456",
        )
        assert sections == []

    def test_missing_fields(self):
        document, sections = parse_uri("dsr://arrete-prefectoral____")
        assert document == Document(
            type=DocumentType.arrete_prefectoral,
            id=None,
            num=None,
            date=None,
            title=None,
        )
        assert sections == []

    def test_with_simple_section(self):
        document, sections = parse_uri(
            "dsr://arrete-prefectoral_123_456_2022-01-01_Arr%C3%AAt%C3%A9%20pr%C3%A9fectoral%20123%20456/article_1_2_3_4"  # noqa: E501
        )
        assert document == Document(
            type=DocumentType.arrete_prefectoral,
            id="123",
            num="456",
            date="2022-01-01",
            title="Arrêté préfectoral 123 456",
        )
        assert sections == [
            Section(
                type=SectionType.article,
                start_id="1",
                start_num="2",
                end_id="3",
                end_num="4",
            )
        ]

    def test_with_section_missing_attributes(self):
        document, sections = parse_uri(
            "dsr://arrete-prefectoral_123_456_2022-01-01_Arr%C3%AAt%C3%A9%20pr%C3%A9fectoral%20123%20456/article_1___"  # noqa: E501
        )
        assert document == Document(
            type=DocumentType.arrete_prefectoral,
            id="123",
            num="456",
            date="2022-01-01",
            title="Arrêté préfectoral 123 456",
        )
        assert sections == [
            Section(
                type=SectionType.article,
                start_id="1",
            )
        ]


class TestValidateSections(unittest.TestCase):

    def test_empty(self):
        _validate_sections([])

    def test_invalid_section_type_order(self):
        with self.assertRaises(ValueError) as context:
            _validate_sections(
                [
                    Section(type=SectionType.alinea, start_id="1"),
                    Section(type=SectionType.article, start_id="1"),
                ],
            )
        assert (
            str(context.exception)
            == f'Section type "{SectionType.article}" is not allowed after "{SectionType.alinea}"'
        )

    def test_end_only_allowed_for_last_section(self):
        with self.assertRaises(ValueError) as context:
            _validate_sections(
                [
                    Section(
                        type=SectionType.article,
                        start_id="1",
                        end_id="2",
                    ),
                    Section(type=SectionType.alinea, start_id="1"),
                ],
            )
        assert str(context.exception) == "End is allowed only for last section"
