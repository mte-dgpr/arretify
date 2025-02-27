from typing import Union, Literal, List, ClassVar
from dataclasses import dataclass
import urllib.parse
from enum import Enum

from bench_convertisseur_xml.types import URI
from bench_convertisseur_xml.law_data.legifrance import get_code_titles


_SEPARATOR = '_'


class SectionType(Enum):
    article = 'article'
    alinea = 'alinea'


class UnknownDocumentTypes(Enum):
    unknown = 'unknown'
    arrete = 'arrete'


class _DocumentBase:
    allowed_section_types: ClassVar[List[SectionType]] = []
    scheme: ClassVar[str] = 'unknown'


@dataclass(frozen=True)
class ArreteMinisteriel(_DocumentBase):
    date: Union[str, None]

    scheme: ClassVar[str] = 'am'
    allowed_section_types: ClassVar[List[SectionType]] = [
        SectionType.article,
        SectionType.alinea,
    ]


@dataclass(frozen=True)
class ArretePrefectoral(_DocumentBase):
    date: Union[str, None]
    code: Union[str, None]

    scheme: ClassVar[str] = 'ap'
    allowed_section_types: ClassVar[List[SectionType]] = [
        SectionType.article,
        SectionType.alinea,
    ]

    def __post_init__(self):
        if self.date is None and self.code is None:
            raise ValueError('Both date and code cannot be None')


@dataclass(frozen=True)
class ArreteUnknown(_DocumentBase):
    """
    Arrete from undefined authority.
    """
    date: str

    scheme: ClassVar[str] = 'unknown'
    allowed_section_types: ClassVar[List[SectionType]] = [
        SectionType.article,
        SectionType.alinea,
    ]


@dataclass(frozen=True)
class Code(_DocumentBase):
    """
    Code juridique (https://www.legifrance.gouv.fr/liste/code)
    """
    title: str

    scheme: ClassVar[str] = 'code'
    allowed_section_types: ClassVar[List[SectionType]] = [
        SectionType.article,
        SectionType.alinea,
    ]

    def __post_init__(self):
        if not self.title in get_code_titles():
            raise ValueError(f'Code "{self.title}" is not in the list of codes')


@dataclass(frozen=True)
class Section:
    type: SectionType
    start: str
    end: Union[str, None] = None

    @classmethod
    def alinea(cls, start: int, end: Union[int, None]=None) -> 'Section':
        return cls(SectionType.alinea, str(start), str(end) if not end is None else None)

    @classmethod
    def article(cls, start: str, end: Union[str, None]=None) -> 'Section':
        return cls(SectionType.article, start, end)


Document = Union[ArretePrefectoral, ArreteMinisteriel, ArreteUnknown, Code]


def render_uri(
    document: Union[Document, None],
    *sections: Section,
) -> URI:
    _validate_sections(document, list(sections))

    # Format for AP URI base : ap://<date>_<code>
    if isinstance(document, ArretePrefectoral):
        document_part = _join_tokens(document.date, document.code)
    
    # Format for AM URI base : am://<date>
    elif isinstance(document, ArreteMinisteriel):
        document_part = _join_tokens(document.date)

    # Format for unknown arrete : unknown://arrete_<date>
    elif isinstance(document, ArreteUnknown):
        document_part = _join_tokens(UnknownDocumentTypes.arrete.value, document.date)

    # Format for code : code://<title>
    elif isinstance(document, Code):
        document_part = _join_tokens(document.title)

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

    scheme_part = document.scheme if document else _DocumentBase.scheme

    return f'{scheme_part}://{document_part}{path}'


def parse_uri(uri: URI) -> tuple[Union[Document, None], List[Section]]:
    scheme_part, rest = uri.split('://', 1)
    
    document: Union[Document, None] = None
    document_part, *section_parts = rest.split('/')

    # Format for AP URI base : ap://<date>_<code>
    if scheme_part == ArretePrefectoral.scheme:
        document_tokens = _split_tokens(document_part)
        if len(document_tokens) != 2:
            raise ValueError(f'Unexpected number of tokens in "{document_part}"')
        document = ArretePrefectoral(date=document_tokens[0], code=document_tokens[1])

    # Format for AM URI base : am://<date>
    elif scheme_part == ArreteMinisteriel.scheme:
        document_tokens = _split_tokens(document_part)
        if len(document_tokens) != 1:
            raise ValueError(f'Unexpected number of tokens in "{document_part}"')
        document = ArreteMinisteriel(date=document_tokens[0])

    # Format for code : code://<title>
    elif scheme_part == Code.scheme:
        document_tokens = _split_tokens(document_part)
        if len(document_tokens) != 1 or document_tokens[0] is None:
            raise ValueError(f'Unexpected tokens in "{document_part}"')
        document = Code(title=document_tokens[0])

    # Format for unknown, or not completely defined document
    elif scheme_part == _DocumentBase.scheme:
        document_tokens = _split_tokens(document_part)
        if len(document_tokens) < 1:
            raise ValueError(f'Unexpected at least one token in "{document_part}"')

        # unknown://arrete_<date>
        if document_tokens[0] == UnknownDocumentTypes.arrete.value:
            if len(document_tokens) != 2 or document_tokens[1] is None:
                raise ValueError(f'Unexpected tokens in "{document_part}"')
            document = ArreteUnknown(date=document_tokens[1])

        # unknown://unknown 
        elif document_tokens[0] == UnknownDocumentTypes.unknown.value:
            document = None

    # Format for articles and alineas part : /<type>_<start>_<end>
    sections: List[Section] = []
    for section_part in section_parts:
        section_tokens = _split_tokens(section_part)
        if len(section_tokens) != 3:
            raise ValueError(f'Unexpected number of tokens in "{section_part}"')
        if section_tokens[1] is None:
            raise ValueError(f'Start is required for section')
        sections.append(
            Section(
                type=SectionType(section_tokens[0]),
                start=section_tokens[1],
                end=section_tokens[2],
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


def _decode(part: str) -> str:
    return urllib.parse.unquote(part)


def _encode(part: str) -> str:
    _assert_allowed_chars(part)
    return urllib.parse.quote(part, safe='')


def _assert_allowed_chars(raw_part: str) -> None:
    if _SEPARATOR in raw_part:
        raise ValueError(f'"{_SEPARATOR}" is not allowed in the part')