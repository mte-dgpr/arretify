import unittest

from .uri import render_uri, parse_uri, ArretePrefectoralDocument, ArreteMinisterielDocument, ArreteUnknownDocument, DecretDocument, CirculaireDocument, CodeDocument, SelfDocument, EuActDocument, SectionType, Section, _validate_sections


class TestRenderUri(unittest.TestCase):

    def test_ap_without_identifier(self):
        uri = render_uri(
            ArretePrefectoralDocument(
                date='2022-01-01',
                identifier=None,
            )
        )
        assert uri == 'ap://2022-01-01_'
    
    def test_ap_with_identifier(self):
        uri = render_uri(
            ArretePrefectoralDocument(
                date='2022-01-01',
                identifier='123',
            )
        )
        assert uri == 'ap://2022-01-01_123'

    def test_ap_with_alineas_start(self):
        uri = render_uri(
            ArretePrefectoralDocument(date='2022-01-01', identifier='123'),
            Section.alinea(1, None),
        )
        assert uri == 'ap://2022-01-01_123/alinea_1_'

    def test_ap_with_alineas_start_end(self):
        uri = render_uri(
            ArretePrefectoralDocument(date='2022-01-01', identifier='123'),
            Section.alinea(1, 2),
        )
        assert uri == 'ap://2022-01-01_123/alinea_1_2'

    def test_ap_with_alinea_negative(self):
        uri = render_uri(
            ArretePrefectoralDocument(date='2022-01-01', identifier='123'),
            Section.alinea(-2, -1),
        )
        assert uri == 'ap://2022-01-01_123/alinea_-2_-1'

    def test_ap_with_articles_and_alineas(self):
        uri = render_uri(
            ArretePrefectoralDocument(date='2022-01-01', identifier='123'),
            Section.article('1'),
            Section.alinea(1, 2),
        )
        assert uri == 'ap://2022-01-01_123/article_1_/alinea_1_2'

    def test_ap_with_special_character_in_section(self):
        uri = render_uri(
            ArretePrefectoralDocument(date='2022-01-01', identifier='123'),
            Section.article('R. 511-9'),
        )
        assert uri == 'ap://2022-01-01_123/article_R.%20511-9_'

    def test_ap_with_special_characters_in_identifier(self):
        uri = render_uri(
            ArretePrefectoralDocument(date='2022-01-01', identifier='123/456 abc'),
        )
        assert uri == 'ap://2022-01-01_123%2F456%20abc'

    def test_render_arrete_ministeriel(self):
        uri = render_uri(
            ArreteMinisterielDocument(date='2022-01-01')
        )
        assert uri == 'am://2022-01-01'

    def test_arrete_unknown(self):
        uri = render_uri(
            ArreteUnknownDocument(date='2022-01-01')
        )
        assert uri == 'unknown://arrete_2022-01-01'

    def test_decret(self):
        uri = render_uri(
            DecretDocument(date='2022-01-01', identifier='123-456')
        )
        assert uri == 'decret://2022-01-01_123-456'

    def test_decret_no_identifier(self):
        uri = render_uri(
            DecretDocument(date='2022-01-01', identifier=None)
        )
        assert uri == 'decret://2022-01-01_'

    def test_circulaire(self):
        uri = render_uri(
            CirculaireDocument(date='2022-01-01', identifier='123-456')
        )
        assert uri == 'circulaire://2022-01-01_123-456'
    
    def test_circulaire_no_identifier(self):
        uri = render_uri(
            CirculaireDocument(date='2022-01-01', identifier=None)
        )
        assert uri == 'circulaire://2022-01-01_'

    def test_code(self):
        uri = render_uri(
            CodeDocument(title='Code de la route')
        )
        assert uri == 'code://Code%20de%20la%20route'

    def test_self(self):
        uri = render_uri(SelfDocument())
        assert uri == 'self://self'
    
    def test_eu_act(self):
        uri = render_uri(
            EuActDocument(act_type='règlement', identifier='1013/2006', domain='CE')
        )
        assert uri == 'eu://r%C3%A8glement_1013%2F2006_CE'

    def test_eu_act_no_domain(self):
        uri = render_uri(
            EuActDocument(act_type='règlement', identifier='1013/2006', domain=None)
        )
        assert uri == 'eu://r%C3%A8glement_1013%2F2006_'

    def test_unknown_document_with_sections(self):
        uri = render_uri(None, Section.alinea(1, 2))
        assert uri == 'unknown://unknown/alinea_1_2'


class TestParseUri(unittest.TestCase):

    def test_ap_without_identifier(self):
        document, sections = parse_uri('ap://2022-01-01_')
        assert document == ArretePrefectoralDocument(date='2022-01-01', identifier=None)
        assert sections == []

    def test_ap_with_identifier(self):
        document, sections = parse_uri('ap://2022-01-01_123')
        assert document == ArretePrefectoralDocument(date='2022-01-01', identifier='123')
        assert sections == []

    def test_ap_with_alineas_start(self):
        document, sections = parse_uri('ap://2022-01-01_123/alinea_1_')
        assert document == ArretePrefectoralDocument(date='2022-01-01', identifier='123')
        assert sections == [Section(type=SectionType.alinea, start='1', end=None)]

    def test_ap_with_alineas_start_end(self):
        document, sections = parse_uri('ap://2022-01-01_123/alinea_1_2')
        assert document == ArretePrefectoralDocument(date='2022-01-01', identifier='123')
        assert sections == [Section(type=SectionType.alinea, start='1', end='2')]

    def test_ap_with_alinea_negative(self):
        document, sections = parse_uri('ap://2022-01-01_123/alinea_-2_-1')
        assert document == ArretePrefectoralDocument(date='2022-01-01', identifier='123')
        assert sections == [Section(type=SectionType.alinea, start='-2', end='-1')]

    def test_ap_with_articles_and_alineas(self):
        document, sections = parse_uri('ap://2022-01-01_123/article_1_/alinea_1_2')
        assert document == ArretePrefectoralDocument(date='2022-01-01', identifier='123')
        assert sections == [
            Section(type=SectionType.article, start='1'),
            Section(type=SectionType.alinea, start='1', end='2'),
        ]

    def test_ap_with_special_character_in_section(self):
        document, sections = parse_uri('ap://2022-01-01_123/article_R.%20511-9_')
        assert document == ArretePrefectoralDocument(date='2022-01-01', identifier='123')
        assert sections == [Section(type=SectionType.article, start='R. 511-9')]

    def test_am(self):
        document, sections = parse_uri('am://2022-01-01')
        assert document == ArreteMinisterielDocument(date='2022-01-01')
        assert sections == []

    def test_arrete_unknown(self):
        document, sections = parse_uri('unknown://arrete_2022-01-01')
        assert document == ArreteUnknownDocument(date='2022-01-01')
        assert sections == []

    def test_decret(self):
        document, sections = parse_uri('decret://2022-01-01_123-456')
        assert document == DecretDocument(date='2022-01-01', identifier='123-456')

    def test_decret_no_identifier(self):
        document, sections = parse_uri('decret://2022-01-01_')
        assert document == DecretDocument(date='2022-01-01', identifier=None)

    def test_circulaire(self):
        document, sections = parse_uri('circulaire://2022-01-01_123-456')
        assert document == CirculaireDocument(date='2022-01-01', identifier='123-456')

    def test_circulaire_no_identifier(self):
        document, sections = parse_uri('circulaire://2022-01-01_')
        assert document == CirculaireDocument(date='2022-01-01', identifier=None)

    def test_code(self):
        document, sections = parse_uri('code://Code%20de%20la%20route')
        assert document == CodeDocument(title='Code de la route')
        assert sections == []

    def test_self(self):
        document, sections = parse_uri('self://self')
        assert document == SelfDocument()

    def test_eu_act(self):
        document, sections = parse_uri('eu://r%C3%A8glement_1013%2F2006_CE')
        assert document == EuActDocument(act_type='règlement', identifier='1013/2006', domain='CE')
        assert sections == []

    def test_eu_act_no_domain(self):
        document, sections = parse_uri('eu://r%C3%A8glement_1013%2F2006_')
        assert document == EuActDocument(act_type='règlement', identifier='1013/2006', domain=None)
        assert sections == []

    def test_unknown_document_with_sections(self):
        document, sections = parse_uri('unknown://unknown/alinea_1_2')
        assert document is None
        assert sections == [Section(type=SectionType.alinea, start='1', end='2')]


class TestValidateSections(unittest.TestCase):

    def test_empty(self):
        _validate_sections(None, [])

    def test_allowed_section_types(self):
        _validate_sections(
            ArretePrefectoralDocument(date='2022-01-01', identifier='123'),
            [
                Section(type=SectionType.article, start='1'),
                Section(type=SectionType.alinea, start='1', end='2'),
            ],
        )

    def test_invalid_section_type_order(self):
        with self.assertRaises(ValueError) as context:
            _validate_sections(
                ArretePrefectoralDocument(date='2022-01-01', identifier='123'),
                [
                    Section(type=SectionType.alinea, start='1'),
                    Section(type=SectionType.article, start='1'),
                ],
            )
        assert str(context.exception) == f'Section type "{SectionType.article}" is not allowed after "{SectionType.alinea}"'

    def test_end_only_allowed_for_last_section(self):
        with self.assertRaises(ValueError) as context:
            _validate_sections(
                ArretePrefectoralDocument(date='2022-01-01', identifier='123'),
                [
                    Section(type=SectionType.article, start='1', end='2'),
                    Section(type=SectionType.alinea, start='1'),
                ],
            )
        assert str(context.exception) == f'End is allowed only for last section'