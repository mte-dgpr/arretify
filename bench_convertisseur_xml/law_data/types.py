from typing import ClassVar, List, Union, Optional
from dataclasses import dataclass
from enum import Enum

from .eurlex_constants import EU_ACT_DOMAINS, EU_ACT_TYPES


class SectionType(Enum):
    article = 'article'
    alinea = 'alinea'


class UnknownDocumentTypes(Enum):
    unknown = 'unknown'
    arrete = 'arrete'


class _DocumentBase:
    allowed_section_types: ClassVar[List[SectionType]] = []
    scheme: ClassVar[str] = ''


@dataclass(frozen=True)
class ArreteMinisterielDocument(_DocumentBase):
    date: str

    scheme: ClassVar[str] = 'am'
    allowed_section_types: ClassVar[List[SectionType]] = [
        SectionType.article,
        SectionType.alinea,
    ]


@dataclass(frozen=True)
class ArretePrefectoralDocument(_DocumentBase):
    date: Union[str, None]
    identifier: Union[str, None]

    scheme: ClassVar[str] = 'ap'
    allowed_section_types: ClassVar[List[SectionType]] = [
        SectionType.article,
        SectionType.alinea,
    ]

    def __post_init__(self):
        if self.date is None and self.identifier is None:
            raise ValueError('Both date and identifier cannot be None')


@dataclass(frozen=True)
class ArreteUnknownDocument(_DocumentBase):
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
class DecretDocument(_DocumentBase):
    date: str
    identifier: Optional[str]

    scheme: ClassVar[str] = 'decret'
    allowed_section_types: ClassVar[List[SectionType]] = [
        SectionType.article,
        SectionType.alinea,
    ]


@dataclass(frozen=True)
class CirculaireDocument(_DocumentBase):
    date: str
    identifier: Optional[str]

    scheme: ClassVar[str] = 'circulaire'
    allowed_section_types: ClassVar[List[SectionType]] = [
        SectionType.article,
        SectionType.alinea,
    ]


@dataclass(frozen=True)
class CodeDocument(_DocumentBase):
    """
    Code juridique (https://www.legifrance.gouv.fr/liste/code)
    """
    title: str

    scheme: ClassVar[str] = 'code'
    allowed_section_types: ClassVar[List[SectionType]] = [
        SectionType.article,
        SectionType.alinea,
    ]


@dataclass(frozen=True)
class SelfDocument(_DocumentBase):
    """
    Self reference.
    """
    scheme: ClassVar[str] = 'self'
    allowed_section_types: ClassVar[List[SectionType]] = [
        SectionType.article,
        SectionType.alinea,
    ]


@dataclass(frozen=True)
class EuActDocument(_DocumentBase):
    """
    EU act. Reference : https://style-guide.europa.eu
    """
    act_type: str
    identifier: str
    domain: Optional[str]

    scheme: ClassVar[str] = 'eu'
    allowed_section_types: ClassVar[List[SectionType]] = [
        SectionType.article,
        SectionType.alinea,
    ]

    def __post_init__(self):
        if self.domain and not self.domain in EU_ACT_DOMAINS:
            raise ValueError(f'Domain "{self.domain}" is not in the list of EU act domains')
        if not self.act_type in EU_ACT_TYPES:
            raise ValueError(f'Act type "{self.act_type}" is not in the list of EU act types')


@dataclass(frozen=True)
class UnknownDocument(_DocumentBase):
    scheme: ClassVar[str] = 'unknown'
    allowed_section_types: ClassVar[List[SectionType]] = [
        SectionType.article,
        SectionType.alinea,
    ]


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


Document = Union[ArretePrefectoralDocument, ArreteMinisterielDocument, ArreteUnknownDocument, DecretDocument, CirculaireDocument, CodeDocument, EuActDocument, SelfDocument]
