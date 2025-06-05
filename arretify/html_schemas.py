from typing import Dict

from .types import DataElementSchema
from dataclasses import replace as dataclass_replace

# TODO : custom DTD for automatic validation of generated document

# -------------------- Parts -------------------- #

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

APPENDIX_SCHEMA = DataElementSchema(
    name="appendix",
    tag_name="appendix",
    data_keys=[],
)

# -------------------- Document schemas -------------------- #

PAGE_FOOTER_SCHEMA = DataElementSchema(
    name="page_footer",
    tag_name="div",
    data_keys=[],
)

TABLE_OF_CONTENTS_SCHEMA = DataElementSchema(
    name="table_of_contents",
    tag_name="div",
    data_keys=[],
)

DOCUMENT_ELEMENTS_SCHEMAS: Dict[str, DataElementSchema] = {
    "page_footer": PAGE_FOOTER_SCHEMA,
    "table_of_contents": TABLE_OF_CONTENTS_SCHEMA,
}

# -------------------- Header schemas -------------------- #

EMBLEM_SCHEMA = DataElementSchema(
    name="emblem",
    tag_name="div",
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

ARRETE_TITLE_SCHEMA = DataElementSchema(
    name="arrete_title",
    tag_name="div",
    data_keys=[],
)

HONORARY_SCHEMA = DataElementSchema(
    name="honorary",
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

SUPPLEMENTARY_MOTIF_INFORMATION_SCHEMA = DataElementSchema(
    name="supplementary_motif_info",
    tag_name="div",
    data_keys=[],
)

HEADER_ELEMENTS_SCHEMAS: Dict[str, DataElementSchema] = {
    "emblem": EMBLEM_SCHEMA,
    "entity": ENTITY_SCHEMA,
    "identification": IDENTIFICATION_SCHEMA,
    "arrete_title": ARRETE_TITLE_SCHEMA,
    "honorary": HONORARY_SCHEMA,
    "visa": VISA_SCHEMA,
    "motif": MOTIF_SCHEMA,
    "supplementary_motif_info": SUPPLEMENTARY_MOTIF_INFORMATION_SCHEMA,
}

# -------------------- Main and appendix schemas -------------------- #

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
SECTION_TITLE6_SCHEMA = dataclass_replace(SECTION_TITLE1_SCHEMA, tag_name="h7")
SECTION_TITLE7_SCHEMA = dataclass_replace(SECTION_TITLE1_SCHEMA, tag_name="h8")
SECTION_TITLE_SCHEMAS = [
    SECTION_TITLE1_SCHEMA,
    SECTION_TITLE2_SCHEMA,
    SECTION_TITLE3_SCHEMA,
    SECTION_TITLE4_SCHEMA,
    SECTION_TITLE5_SCHEMA,
    SECTION_TITLE6_SCHEMA,
    SECTION_TITLE7_SCHEMA,
]

ALINEA_SCHEMA = DataElementSchema(
    name="alinea",
    tag_name="div",
    data_keys=["number"],
)

# -------------------- References schemas -------------------- #

DOCUMENT_REFERENCE_SCHEMA = DataElementSchema(
    name="document_reference",
    tag_name="a",
    data_keys=["uri", "is_resolvable"],
)

SECTION_REFERENCE_SCHEMA = DataElementSchema(
    name="section_reference",
    tag_name="a",
    data_keys=["uri", "is_resolvable", "parent_reference"],
)

DATE_SCHEMA = DataElementSchema(
    name="date",
    tag_name="time",
    data_keys=[],
)

# -------------------- Operations schemas -------------------- #

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

# -------------------- Errors schemas -------------------- #

ERROR_SCHEMA = DataElementSchema(
    name="error",
    tag_name="span",
    data_keys=[],
)

DEBUG_KEYWORD_SCHEMA = DataElementSchema(
    name="debug_keyword",
    tag_name="span",
    data_keys=["query"],
)
