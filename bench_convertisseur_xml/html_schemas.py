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
    data_keys=["title", "number", "type"],
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
    data_keys=["number"],
)

DOCUMENT_REFERENCE_SCHEMA = DataElementSchema(
    name="document_reference",
    tag_name="a",
    data_keys=["uri", "is_resolvable"],
)

SECTION_REFERENCE_SCHEMA = DataElementSchema(
    name="section_reference",
    tag_name="a",
    data_keys=["uri", "is_resolvable"],
)

SECTION_REFERENCE_MULTIPLE_SCHEMA = DataElementSchema(
    name="section_reference_multiple",
    tag_name="span",
    data_keys=[],
)
"""
A group of section references to the same document.
"""

SECTIONS_AND_DOCUMENT_REFERENCES = DataElementSchema(
    name="sections_and_document_references",
    tag_name="span",
    data_keys=[],
)
"""
A group of sections references and their associated document reference.
"""

DATE_SCHEMA = DataElementSchema(name="date", tag_name="time", data_keys=[])

ERROR_SCHEMA = DataElementSchema(
    name="error",
    tag_name="span",
    data_keys=["error_code"],
)

OPERATION_SCHEMA = DataElementSchema(
    name="operation",
    tag_name="span",
    data_keys=[
        "operation_type",
        "direction",
        "keyword",
        "has_operand",
        "references",
        "operand",
    ],
)

DEBUG_KEYWORD_SCHEMA = DataElementSchema(
    name="debug_keyword",
    tag_name="span",
    data_keys=["query"],
)
