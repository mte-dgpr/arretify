from bs4 import BeautifulSoup, Tag

from arretify.utils.html import make_data_tag
from arretify.html_schemas import ALINEA_SCHEMA, SECTION_SCHEMA, SECTION_TITLE_SCHEMAS
from arretify.parsing_utils.source_mapping import TextSegments
from arretify.regex_utils import PatternProxy
from .types import GroupParsingContext, BodySection
from .basic_elements import parse_basic_elements


APPENDIX_PATTERN = PatternProxy(r"^annexe")


def is_appendix_title(line: str) -> bool:
    return bool(APPENDIX_PATTERN.match(line))


def parse_appendix(soup: BeautifulSoup, appendix: Tag, lines: TextSegments) -> TextSegments:

    appendix_count = 0

    while lines:

        appendix_count += 1

        title_contents = lines.pop(0).contents

        section_element = make_data_tag(
            soup,
            SECTION_SCHEMA,
            data=dict(
                type=BodySection.APPENDIX.value,
                number=str(appendix_count),
                title=title_contents,
            ),
        )
        appendix.append(section_element)

        title_element = make_data_tag(
            soup,
            SECTION_TITLE_SCHEMAS[0],
            contents=[title_contents],
        )
        section_element.append(title_element)

        appendix_context = GroupParsingContext(alinea_count=0)

        # TODO: add handling of sections inside appendices
        # Why is it hard? there can be subappendices
        while lines and not is_appendix_title(lines[0].contents):

            appendix_context.alinea_count += 1
            alinea_element = make_data_tag(
                soup,
                ALINEA_SCHEMA,
                data=dict(number=str(appendix_context.alinea_count)),
            )
            section_element.append(alinea_element)
            parse_basic_elements(soup, alinea_element, lines)

    return lines
