from .types import ElementSchema

ARRETE_SCHEMA = ElementSchema(
    name="arrete",
    tag_name="span",
    classes=["dsr-arrete"],
    data_keys=['code', 'qualifier', 'authority'],
)

DATE_SCHEMA = ElementSchema(
    name="date",
    tag_name="time",
    classes=["dsr-date"],
    data_keys=[]
)