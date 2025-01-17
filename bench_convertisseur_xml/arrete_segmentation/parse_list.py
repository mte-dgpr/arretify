from typing import List
import re

from bs4 import BeautifulSoup, Tag

from bench_convertisseur_xml.utils.html import PageElementOrString, make_ul, make_li
from .sentence_rules import is_liste, LIST_PATTERN


BULLET_LIST_RE = re.compile(r'^\s*-\s*')


def list_indentation(line: str):
    list_match = LIST_PATTERN.match(line)
    if not list_match:
        raise ValueError("Expected line to be a list element")
    return len(list_match.group('indentation'))


def clean_bullet_list(line: str):
    return BULLET_LIST_RE.sub('', line)


# TODO : deal with case :
# - bla
#     hello
#     hellu
# - bli
def parse_list(soup: BeautifulSoup, lines: List[str]):
    list_pile: List[PageElementOrString] = []
    ref_indentation =  list_indentation(lines[0])
    
    while lines and is_liste(lines[0]):
        current_indentation = list_indentation(lines[0])
        if current_indentation == ref_indentation:
            line = lines.pop(0)
            if isinstance(line, str):
                line = clean_bullet_list(line)
            list_pile.append(line)

        elif current_indentation > ref_indentation:
            lines, nested_ul = parse_list(soup, lines)
            li = make_li(soup, [list_pile.pop(), nested_ul])
            list_pile.append(li)
        
        else:
            break

    return lines, make_ul(soup, list_pile)