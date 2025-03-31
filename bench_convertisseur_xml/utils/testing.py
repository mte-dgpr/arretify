from typing import Callable, List, Iterable

from bs4 import Tag, BeautifulSoup, PageElement

from bench_convertisseur_xml.types import PageElementOrString


def make_element_processor(process_function: Callable[[Tag], None]) -> Callable[[str], str]:
    def _element_processor(string: str) -> str:
        soup = BeautifulSoup(string, features='html.parser')
        tag_list = soup.select('*')
        if not tag_list or not isinstance(tag_list[0], Tag):
            raise ValueError('No tag found')
        tag = tag_list[0]
        process_function(tag)
        return str(tag)
    return _element_processor


def make_children_processor(process_function: Callable[[BeautifulSoup, Iterable[PageElementOrString]], List[PageElementOrString]]) -> Callable[[str], str]:
    def _children_processor(string: str):
        soup = BeautifulSoup(string, features='html.parser')
        elements = process_function(soup, soup.children)
        return [str(element) for element in elements]
    return _children_processor
