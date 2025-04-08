from typing import Callable, List, Iterable

from bs4 import Tag, BeautifulSoup, PageElement

from bench_convertisseur_xml.types import PageElementOrString


def make_testing_function_for_single_tag(
    process_function: Callable[[Tag], None]
) -> Callable[[str], str]:
    def _testing_function(string: str, css_selector: str | None=None) -> str:
        soup = create_bs(string)

        tag_list: List[PageElement]
        if css_selector is None:
            tag_list = list(soup.children)
        else:
            tag_list = list(soup.select(css_selector))

        if len(tag_list) != 1:
            raise ValueError('One and only one tag must be found')

        if not isinstance(tag_list[0], Tag):
            raise ValueError('No tag found')
        
        tag = tag_list[0]
        process_function(tag)
        return str(tag)
    return _testing_function


def make_testing_function_for_children_list(
    process_function: Callable[[BeautifulSoup, Iterable[PageElementOrString]], List[PageElementOrString]]
) -> Callable[[str], str]:
    def _testing_function(string: str):
        soup = create_bs(string)
        elements = process_function(soup, soup.children)
        return [str(element) for element in elements]
    return _testing_function


def create_bs(html: str) -> BeautifulSoup:
    return BeautifulSoup(html.replace('\n', '').replace('    ', ''), features='html.parser')