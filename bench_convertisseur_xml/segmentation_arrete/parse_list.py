from typing import List
import re

from bs4 import BeautifulSoup, Tag

from bench_convertisseur_xml.utils.html import PageElementOrString, make_ul
from .sentence_rules import is_liste


BULLET_LIST_RE = re.compile(r'^\s*-\s*')


def clean_bullet_list(line: str):
    return BULLET_LIST_RE.sub('', line)


def parse_list(soup: BeautifulSoup, lines: List[str]):
    list_pile: List[PageElementOrString] = []
    while lines and is_liste(lines[0]):
        line = lines.pop(0)
        if isinstance(line, str):
            line = clean_bullet_list(line)
        list_pile.append(line)
    return lines, make_ul(soup, list_pile)