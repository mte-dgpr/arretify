from .types import DataElementSchema
from dataclasses import replace as dataclass_replace

# TODO : custom DTD for automatic validation of generated document

HEADER_SCHEMA = DataElementSchema(
    name="header",
    tag_name="header",
    data_keys=[],
)

MAIN_SCHEMA = DataElementSchema(
    name="main",
    tag_name="main",
    data_keys=[],
)

ENTITY_SCHEMA = DataElementSchema(
    name="entity",
    tag_name="div",
    data_keys=[],
)

IDENTIFICATION_SCHEMA = DataElementSchema(
    name="identification",
    tag_name="div",
    data_keys=[],
)

VISA_SCHEMA = DataElementSchema(
    name="visa",
    tag_name="div",
    data_keys=[],
)

MOTIF_SCHEMA = DataElementSchema(
    name="motifs",
    tag_name="div",
    data_keys=[],
)

SECTION_SCHEMA = DataElementSchema(
    name="section",
    tag_name="section",
    data_keys=['title', 'number', 'type'],
)

SECTION_TITLE1_SCHEMA = DataElementSchema(
    name="section_title",
    tag_name="h2",
    data_keys=[],
)
SECTION_TITLE2_SCHEMA = dataclass_replace(SECTION_TITLE1_SCHEMA, tag_name="h3")
SECTION_TITLE3_SCHEMA = dataclass_replace(SECTION_TITLE1_SCHEMA, tag_name="h4")
SECTION_TITLE4_SCHEMA = dataclass_replace(SECTION_TITLE1_SCHEMA, tag_name="h5")
SECTION_TITLE5_SCHEMA = dataclass_replace(SECTION_TITLE1_SCHEMA, tag_name="h6")
SECTION_TITLE_SCHEMAS = [
    SECTION_TITLE1_SCHEMA,
    SECTION_TITLE2_SCHEMA,
    SECTION_TITLE3_SCHEMA,
    SECTION_TITLE4_SCHEMA,
    SECTION_TITLE5_SCHEMA,
]


ALINEA_SCHEMA = DataElementSchema(
    name="alinea",
    tag_name="div",
    data_keys=['number'],
)

ARRETE_REFERENCE_SCHEMA = DataElementSchema(
    name="arrete_reference",
    tag_name="a",
    data_keys=['code', 'qualifier', 'authority'],
)

TARGET_POSITION_REFERENCE_SCHEMA = DataElementSchema(
    name="target_position_reference",
    tag_name="a",
    data_keys=['article_start', 'article_end', 'section_start', 'section_end'],
)

DATE_SCHEMA = DataElementSchema(
    name="date",
    tag_name="time",
    data_keys=[]
)

ERROR_SCHEMA = DataElementSchema(
    name='error',
    tag_name='span',
    data_keys=['error_code'],
)

MODIFICATION_SEGMENT_SCHEMA = DataElementSchema(
    name='modification_segment',
    tag_name='span',
    data_keys=['modification_type', 'keyword'],
)

DEBUG_KEYWORD_SCHEMA = DataElementSchema(
    name="debug_keyword",
    tag_name="span",
    data_keys=['query'],
)