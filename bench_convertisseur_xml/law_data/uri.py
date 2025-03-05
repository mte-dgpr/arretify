from typing import Union, Literal, List, ClassVar, Optional, Tuple, cast
from dataclasses import dataclass
import urllib.parse
from enum import Enum

from bench_convertisseur_xml.types import URI
from bench_convertisseur_xml.law_data.legifrance import get_code_titles
from .types import SectionType, Section, Document, ArretePrefectoralDocument, ArreteMinisterielDocument, ArreteUnknownDocument, DecretDocument, CirculaireDocument, CodeDocument, EuActDocument, SelfDocument, UnknownDocumentTypes, UnknownDocument


_SEPARATOR = '_'


def render_uri(
    document: Union[Document, None],
    *sections: Section,
) -> URI:
    _validate_sections(document, list(sections))

    # Format for AP URI base : ap://<date>_<identifier>
    if isinstance(document, ArretePrefectoralDocument):
        document_part = _join_tokens(document.date, document.identifier)
    
    # Format for AM URI base : am://<date>
    elif isinstance(document, ArreteMinisterielDocument):
        document_part = _join_tokens(document.date)

    # Format for unknown arrete : unknown://arrete_<date>
    elif isinstance(document, ArreteUnknownDocument):
        document_part = _join_tokens(UnknownDocumentTypes.arrete.value, document.date)

    # Format for decret : decret://<date>_<identifier>
    elif isinstance(document, DecretDocument):
        document_part = _join_tokens(document.date, document.identifier)

    # Format for circulaire : circulaire://<date>_<identifier>
    elif isinstance(document, CirculaireDocument):
        document_part = _join_tokens(document.date, document.identifier)

    # Format for code : code://<title>
    elif isinstance(document, CodeDocument):
        document_part = _join_tokens(document.title)

    # Format for EU act : eu://<act_type>_<identifier>_<domain>
    elif isinstance(document, EuActDocument):
        document_part = _join_tokens(document.act_type, document.identifier, document.domain)

    # Format for self reference : self://self
    elif isinstance(document, SelfDocument):
        document_part = 'self'

    # Format for unknown document : unknown://unknown
    elif document is None:
        document_part = _join_tokens(UnknownDocumentTypes.unknown.value)

    # Format for articles and alineas part : /<type>_<start>_<end>
    path = ''
    for section in sections:
        if not document or section.type in document.allowed_section_types:
            section_part = _join_tokens(section.type.value, section.start, section.end)
            path += f'/{section_part}'
        else:
            raise ValueError(f'Unsupported section type "{section.type}"')

    scheme_part = document.scheme if document else UnknownDocument.scheme

    return f'{scheme_part}://{document_part}{path}'


def parse_uri(uri: URI) -> tuple[Union[Document, None], List[Section]]:
    scheme_part, rest = uri.split('://', 1)
    
    document: Union[Document, None] = None
    document_part, *section_parts = rest.split('/')

    # Format for AP URI base : ap://<date>_<identifier>
    if scheme_part == ArretePrefectoralDocument.scheme:
        _, (date, identifier) = _load_tokens(document_part, optional=[0, 1])
        document = ArretePrefectoralDocument(date=date, identifier=identifier)

    # Format for AM URI base : am://<date>
    elif scheme_part == ArreteMinisterielDocument.scheme:
        (date,), _ = _load_tokens(document_part, required=[0])
        document = ArreteMinisterielDocument(date=date)

    # Format for decret : decret://<date>_<identifier>
    elif scheme_part == DecretDocument.scheme:
        (date,), (identifier,) = _load_tokens(document_part, required=[0], optional=[1])
        document = DecretDocument(date=date, identifier=identifier)

    # Format for circulaire : circulaire://<date>_<identifier>
    elif scheme_part == CirculaireDocument.scheme:
        (date,), (identifier,) = _load_tokens(document_part, required=[0], optional=[1])
        document = CirculaireDocument(date=date, identifier=identifier)

    # Format for code : code://<title>
    elif scheme_part == CodeDocument.scheme:
        (title,), _ = _load_tokens(document_part, required=[0])
        document = CodeDocument(title=title)

    # Format for EU act : eu://<act_type>_<identifier>_<domain>
    elif scheme_part == EuActDocument.scheme:
        (act_type, identifier), (domain,) = _load_tokens(document_part, required=[0, 1], optional=[2])
        document = EuActDocument(act_type=act_type, identifier=identifier, domain=domain)

    # Format for self reference : self://self
    elif scheme_part == SelfDocument.scheme:
        document = SelfDocument()

    # Format for unknown, or not completely defined document
    elif scheme_part == UnknownDocument.scheme:
        (document_type,), _ = _load_tokens(document_part, required=[0])

        # unknown://arrete_<date>
        if document_type == UnknownDocumentTypes.arrete.value:
            (date,), _ = _load_tokens(document_part, required=[1])
            document = ArreteUnknownDocument(date=date)

        # unknown://unknown 
        elif document_type == UnknownDocumentTypes.unknown.value:
            document = None

    # Format for articles and alineas part : /<type>_<start>_<end>
    sections: List[Section] = []
    for section_part in section_parts:
        (section_type, start), (end,) = _load_tokens(section_part, required=[0, 1], optional=[2])
        sections.append(
            Section(
                type=SectionType(section_type),
                start=start,
                end=end,
            )
        )

    _validate_sections(document, list(sections))
    return document, sections


def _validate_sections(document: Union[Document, None], sections: List[Section]) -> None:
    allowed_section_types: List[SectionType] = document.allowed_section_types if document else list(SectionType)

    for i, section in enumerate(sections):
        if section.type not in allowed_section_types:
            raise ValueError(f'Unsupported section type "{section.type}"')
        
        if i < len(sections) - 1:
            if not section.end is None:
                raise ValueError(f'End is allowed only for last section')
            
        if i > 0:
            previous_section = sections[i - 1]
            previous_section_type_index = allowed_section_types.index(previous_section.type)
            section_type_index = allowed_section_types.index(section.type)
            if section_type_index < previous_section_type_index:
                raise ValueError(f'Section type "{section.type}" is not allowed after "{previous_section.type}"')


def _join_tokens(*tokens: Union[str, None]) -> str:
    return _SEPARATOR.join([_encode(token) if token else '' for token in tokens])


def _split_tokens(part: str) -> List[Union[str, None]]:
    return [_decode(token) or None for token in part.split(_SEPARATOR)]


def _load_tokens(part: str, required: List[int]=[], optional: List[int]=[]) -> Tuple[List[str], List[Union[str, None]]]:
    tokens = _split_tokens(part)
    try:
        required_tokens = [tokens[i] for i in required]
        optional_tokens = [tokens[i] for i in optional]
    except IndexError:
        raise ValueError(f'Unexpected token format in "{part}"')
    if None in required_tokens:
        raise ValueError(f'Required token is missing in "{part}"')

    return cast(List[str], required_tokens), optional_tokens


def _decode(part: str) -> str:
    return urllib.parse.unquote(part)


def _encode(part: str) -> str:
    _assert_allowed_chars(part)
    return urllib.parse.quote(part, safe='')


def _assert_allowed_chars(raw_part: str) -> None:
    if _SEPARATOR in raw_part:
        raise ValueError(f'"{_SEPARATOR}" is not allowed in the part')