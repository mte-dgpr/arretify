from typing import List, Tuple, Callable
import re

from bs4 import BeautifulSoup, Tag

from bench_convertisseur_xml.utils.html import PageElementOrString, make_ul, make_li, wrap_in_tag
from bench_convertisseur_xml.utils.markdown import parse_markdown_table, is_table_line
from bench_convertisseur_xml.errors import ParsingError, ErrorCodes
from .sentence_rules import is_liste, is_table_description, is_blockquote_start, is_blockquote_end, LIST_PATTERN
from bench_convertisseur_xml.parsing_utils.source_mapping import TextSegments, apply_to_segment


BULLET_LIST_RE = re.compile(r'^\s*-\s*')


def parse_basic_elements(
    soup: BeautifulSoup, 
    container: Tag, 
    lines: TextSegments,
    render_default: Callable[[str], List[PageElementOrString]] = lambda string: [string]
):
    if is_table_line(lines[0].contents):
        lines, table_elements = parse_table(soup, lines)
        container.extend(table_elements)
        
    elif is_liste(lines[0].contents):
        lines, ul_element = parse_list(soup, lines)
        container.append(ul_element)

    elif is_blockquote_start(lines[0].contents):
        lines, blockquote_element = parse_blockquote(soup, lines)
        container.append(blockquote_element)

    # Normal paragraph
    else:
        container.extend(render_default(lines.pop(0).contents))


def list_indentation(line: str):
    list_match = LIST_PATTERN.match(line)
    if not list_match:
        raise ValueError("Expected line to be a list element")
    indentation = list_match.group('indentation')
    assert indentation is not None
    return len(indentation)


def _clean_bullet_list(line: str):
    return BULLET_LIST_RE.sub('', line)


# TODO : deal with case :
# - bla
#     hello
#     hellu
# - bli
def parse_list(
    soup: BeautifulSoup, 
    lines: TextSegments
) -> Tuple[TextSegments, PageElementOrString]:
    list_pile: List[PageElementOrString] = []
    ref_indentation =  list_indentation(lines[0].contents)
    
    while lines and is_liste(lines[0].contents):
        current_indentation = list_indentation(lines[0].contents)
        if current_indentation == ref_indentation:
            line = apply_to_segment(lines.pop(0), _clean_bullet_list)
            list_pile.append(line.contents)

        elif current_indentation > ref_indentation:
            lines, nested_ul = parse_list(soup, lines)
            li = make_li(soup, [list_pile.pop(), nested_ul])
            list_pile.append(li)
        
        else:
            break

    return lines, make_ul(soup, list_pile)


def parse_table(
    soup: BeautifulSoup,
    lines: TextSegments,
) -> Tuple[TextSegments, List[PageElementOrString]]:
    pile: List[PageElementOrString] = []
    elements: List[PageElementOrString] = []

    while lines and is_table_line(lines[0].contents):
        pile.append(lines.pop(0).contents)
    elements.append(parse_markdown_table(pile))

    while lines and is_table_description(lines[0].contents, pile):
        elements.append(soup.new_tag('br'))
        elements.append(lines.pop(0).contents)

    return lines, elements


def parse_blockquote(
    soup: BeautifulSoup,
    lines: TextSegments
) -> Tuple[TextSegments, Tag]:
    pile: TextSegments = []

    if not is_blockquote_start(lines[0].contents):
        raise RuntimeError("Expected block quote start")

    while lines and not is_blockquote_end(lines[0].contents):
        pile.append(lines.pop(0))
    if not lines:
        raise ParsingError(
            ErrorCodes.unbalanced_quote,
            line_col=pile[0].start,
        )
    
    pile.append(lines.pop(0))

    # Remove the quote start and end
    # TODO-PROCESS-TAG
    pile[0] = apply_to_segment(pile[0], lambda string: string[1:])
    pile[-1] = apply_to_segment(pile[-1], lambda string: string[:-1])

    blockquote = soup.new_tag('blockquote')

    while pile:
        parse_basic_elements(
            soup, 
            blockquote, 
            pile, 
            lambda string: wrap_in_tag(soup, [string], 'p')
        )

    return lines, blockquote
