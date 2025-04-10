import re
from typing import List, cast

import markdown
from bs4 import BeautifulSoup
from pylatexenc.latex2text import LatexNodes2Text

from bench_convertisseur_xml.errors import ErrorCodes
from bench_convertisseur_xml.utils.html import PageElementOrString, make_data_tag
from bench_convertisseur_xml.regex_utils import sub_with_match
from bench_convertisseur_xml.html_schemas import ERROR_SCHEMA
from bench_convertisseur_xml.arrete_segmentation.sentence_rules import LIST_PATTERN
from bench_convertisseur_xml.parsing_utils.source_mapping import TextSegment, apply_to_segment


LATEX_NODE = LatexNodes2Text(keep_comments=True)


def parse_markdown_table(elements: List[PageElementOrString]):
    if [element for element in elements if not isinstance(element, str)]:
        raise ValueError('got unexpected non-string element to parse markdown from')

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


def parse_markdown_image(element: PageElementOrString):
    if not isinstance(element, str):
        raise ValueError('got unexpected non-string element to parse markdown from')

    html_str = markdown.markdown(element)
    soup = BeautifulSoup(html_str, features='html.parser')
    image_element = soup.select('img')[0]

    return image_element


def convert_latex(match) -> str:

    contents = match.group(1)

    # Remove any '\\'
    # This is a pre-requisite to perform LaTeX conversion
    contents = re.sub(r'\\{2,}', '', contents)

    # Convert LaTeX OCR to plain text
    contents = LATEX_NODE.latex_to_text(contents)

    # Convert all _n to small n
    # This is a supplementary stpe to process remnants of LaTeX conversion
    def underscript_numbers_replacement(match):
        underscripts = '₀₁₂₃₄₅₆₇₈₉'
        return underscripts[int(match.group(1))]
    contents = re.sub(r'_([0-9])', underscript_numbers_replacement, contents)

    # Remove any ^ if not followed by a number
    # This is a supplementary step to process remnants of LaTeX conversion
    contents = re.sub(r'\^(?![0-9])', '', contents)

    # Convert all ^n to upper n
    # This is a supplementary stpe to process remnants of LaTeX conversion
    def superscript_numbers_replacement(match):
        superscripts = {
            '0': '⁰',
            '1': '¹',
            '2': '²',
            '3': '³',
            '4': '⁴',
            '5': '⁵',
            '6': '⁶',
            '7': '⁷',
            '8': '⁸',
            '9': '⁹'
        }
        return superscripts[match.group(1)]
    contents = re.sub(r'\^([0-9])', superscript_numbers_replacement, contents)

    # Convert any '∘' to '°'
    # This is a supplementary step to process remnants of LaTeX conversion
    contents = re.sub(r'∘', '°', contents)

    return contents


# TODO-PROCESS-TAG
def clean_markdown(line: TextSegment) -> TextSegment:

    # Remove newline at the end
    line = apply_to_segment(line, lambda contents: re.sub(r'[\n\r]+$', '', contents))

    # Remove * at the beginning only if matching closing * found
    matched_em_open = re.search(r"^\s*(?P<em_open>\*+)(?!\s)", line.contents)

    line_mem: TextSegment
    if matched_em_open:
        asterisk_count = len(matched_em_open.group('em_open'))
        line_mem = line
        line = apply_to_segment(
            line, lambda contents: sub_with_match(contents, matched_em_open, 'em_open')
        )
        matched_em_close = re.search(
            r"\s*(?P<em_close>\*" + f"{{{asterisk_count}}})\b*", line.contents
        )
        # If there's no matching closing asterisks, we restore the line
        if not matched_em_close or matched_em_close.start() == 0:
            line = line_mem
        else:
            line = apply_to_segment(
                line, lambda contents: sub_with_match(contents, matched_em_close, 'em_close')
            )

    # Remove any number of # or whitespaces at the beginning of the sentence
    if not LIST_PATTERN.match(line.contents):
        line = apply_to_segment(line, lambda contents: re.sub(r"^\s*[#\s]+", "", contents))

    # Convert from latex to plain text
    line = apply_to_segment(
        line, lambda contents: re.sub(r'\$(.*?)\$', convert_latex, contents)
    )

    # Convert OCR errors
    ocr_replacements = {
        r'N̊': 'n°',
        r'ı': 'i',
        r'pğ̣': 'pg',
        r'é́': 'é',
        r'ó́': 'oï',
        r'ś́': 's',
        r'Nํ': 'N°',
    }
    for wrong, correct in ocr_replacements.items():
        line = apply_to_segment(line, lambda contents: re.sub(wrong, correct, contents))

    # Resolve diacritics
    line = apply_to_segment(
        line, lambda contents: re.sub(r'([a-zA-Z])[\u0300-\u036F]{1,}', r'\1', contents)
    )

    return line


def is_table_line(line: str) -> bool:
    """Detect if the line is part of a table."""
    # Any | character to detect a table
    return bool(re.search(r"(\|)", line, re.IGNORECASE))
