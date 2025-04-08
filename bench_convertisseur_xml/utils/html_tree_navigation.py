from typing import List

from bs4 import Tag, PageElement


def closest_common_ancestor(*elements: PageElement) -> Tag:
    if len(elements) < 2:
        raise ValueError('At least two elements are required')
    
    for parent in elements[0].parents:
        # Standard `in` operator uses value equality `==` for comparison.
        # For two tags this is not satisfying because for example two empty divs
        # will appear equal even if they are in a completely different place in the tree.
        if all(
            any(other_parent is parent for other_parent in element.parents)
            for element in elements[1:]
        ):
            return parent
    raise ValueError('No common parent found')


def is_descendant(child: PageElement, parent: PageElement) -> bool:
    if not isinstance(parent, Tag):
        return False
    for descendant in parent.descendants:
        if child is descendant:
            return True
    return False


def is_parent(parent: PageElement, child: PageElement) -> bool:
    if not isinstance(parent, Tag):
        return False
    for ancestor in child.parents:
        if parent is ancestor:
            return True
    return False