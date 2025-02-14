import re
from typing import List, cast

import markdown
from bs4 import BeautifulSoup

from bench_convertisseur_xml.errors import ErrorCodes
from bench_convertisseur_xml.utils.html import PageElementOrString, make_data_tag
from bench_convertisseur_xml.regex_utils import sub_with_match
from bench_convertisseur_xml.html_schemas import ERROR_SCHEMA
from bench_convertisseur_xml.arrete_segmentation.sentence_rules import LIST_PATTERN
from bench_convertisseur_xml.parsing_utils.source_mapping import TextSegment, apply_to_segment


def parse_markdown_table(elements: List[PageElementOrString]):
    if [element for element in elements if not isinstance(element, str)]:
        raise ValueError(f'got unexpected non-string element to parse markdown from')

    markdown_str = '\n'.join(cast(List[str], elements))
    html_str = markdown.markdown(markdown_str, extensions=['tables'])
    soup = BeautifulSoup(html_str, features="html.parser")
    table_result = soup.select('table')
    if len(table_result) != 1:
        return make_data_tag(
            soup, 
            ERROR_SCHEMA, 
            data=dict(error_code=ErrorCodes.markdown_parsing.value), contents=[markdown_str]
        )
    
    table_element = soup.new_tag('table')
    table_element.extend(list(table_result[0].children))
    return table_element


# TODO-PROCESS-TAG
def clean_markdown(line: TextSegment) -> TextSegment:
    # Remove newline at the end
    line = apply_to_segment(line, lambda contents: re.sub(r'[\n\r]+$', '', contents))
    line_mem: TextSegment

    # Remove * at the beginning only if matching closing * found
    matched_em_open = re.search(r"^\s*(?P<em_open>\*+)(?!\s)", line.contents)
    if matched_em_open:
        asterisk_count = len(matched_em_open.group('em_open'))
        line_mem = line
        line = apply_to_segment(line, lambda contents: sub_with_match(contents, matched_em_open, 'em_open'))
        matched_em_close = re.search(r"\s*(?P<em_close>\*" + f"{{{asterisk_count}}})\b*", line.contents)
        # If there's no matching closing asterisks, we restore the line
        if not matched_em_close or matched_em_close.start() == 0:
            line = line_mem
        else:
            line = apply_to_segment(line, lambda contents: sub_with_match(contents, matched_em_close, 'em_close'))

    # Remove any number of # or whitespaces at the beginning of the sentence
    if not LIST_PATTERN.match(line.contents):
        line = apply_to_segment(line, lambda contents: re.sub(r"^\s*[#\s]+", "", contents))

    return line


def is_table_line(line: str) -> bool:
    """Detect if the line is part of a table."""
    # Any | character to detect a table
    return bool(re.search(r"(\|)", line, re.IGNORECASE))
