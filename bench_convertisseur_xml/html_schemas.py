from .types import DataElementSchema, PresentationElementSchema

# TODO : custom DTD for automatic validation of generated document

# -------- Data element schemas
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

MOTIFS_SCHEMA = DataElementSchema(
    name="motifs",
    tag_name="div",
    data_keys=[],
)

SECTION_SCHEMA = DataElementSchema(
    name="section",
    tag_name="section",
    data_keys=['title', 'number', 'type'],
)

SECTION_TITLE_SCHEMA = DataElementSchema(
    name="section_title",
    tag_name="p",
    data_keys=[],
)

ARRETE_SCHEMA = DataElementSchema(
    name="arrete",
    tag_name="a",
    data_keys=['code', 'qualifier', 'authority'],
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


# -------- Presentational schemas
DIV_SCHEMA = PresentationElementSchema(
    tag_name="div",
)

TABLE_SCHEMA = PresentationElementSchema(
    tag_name="table",
)

PARAGRAPH_SCHEMA = PresentationElementSchema(
    tag_name="p",
)

LIST_SCHEMA = PresentationElementSchema(
    tag_name="div",
)