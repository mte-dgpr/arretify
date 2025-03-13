from typing import Callable, List, Tuple, Iterator

from bs4 import BeautifulSoup, Tag, PageElement


ElementRange = List[PageElement]
"""
A range of elements which follow each other in parsing order. e.g. : 

    <div id="el1"></div>
    <div id="el2">
        <div id="el3"></div>
    </div>
    <div id="el4"></div>

[el1, el2, el3] is a valid element range.
[el1, el3] is also a valid element range.
[el1, el2, el4] is not a valid element range.
"""


def iter_collapsed_range_right(
    start_tag: Tag, 
) -> Iterator[ElementRange]:
    all_elements: ElementRange = [start_tag]
    current = _find_next_after(start_tag)
    while current:
        collapsed = _collapse_element_range(all_elements)
        # If the last element is parent of `current`, 
        # it means we are going down in the tree, so `current`
        # is a leaf and we don't want to collapse it, even if it
        # is the only node of its parent.
        if _is_parent(collapsed[-1], current):
            collapsed.pop()
        yield collapsed + [current]
        all_elements.append(current)
        current = current.next_element


def iter_collapsed_range_left(
    start_tag: Tag,
) -> Iterator[ElementRange]:
    all_elements: ElementRange = [start_tag]
    current = start_tag.previous_element
    current_range: ElementRange
    previous_range: None | ElementRange = None
    while current:
        current_range = _collapse_element_range([current] + all_elements)
        if previous_range is None:
            yield current_range
        elif current_range != previous_range:
            yield current_range
        previous_range = current_range
        all_elements.insert(0, current)
        current = current.previous_element


def _is_descendant(child: PageElement, parent: PageElement) -> bool:
    if not isinstance(parent, Tag):
        return False
    for descendant in parent.descendants:
        if child is descendant:
            return True
    return False


def _is_parent(parent: PageElement, child: PageElement) -> bool:
    if not isinstance(parent, Tag):
        return False
    for ancestor in child.parents:
        if parent is ancestor:
            return True
    return False


def _find_next_after(element: PageElement) -> PageElement | None:
    if element.next_sibling:
        return element.next_sibling
    else:
        next_element = element.next_element
        while next_element and _is_descendant(next_element, element):
            next_element = next_element.next_element
        return next_element


def _collapse_element_range(element_range: ElementRange) -> ElementRange:
    """
    Collapses an ElementRange into a list of elements that are not parent of each other.

    There are mostly two cases : 

    Consider the following html structure :

            <div id="el1">
                <div id="el2"></div>
            </div>
            <div id="el3"></div>
            <div id="el4">
                <div id="el5">
                    <div id="el6"></div>
                    <div id="el7"></div>
                </div>
            </div>

    1. Complete sub trees are collapsed into their root node. e.g., collapsing the range :

            <div id="el1">
                <div id="el2"></div>
            </div>
            <div id="el3"></div>

        gives :

            <div id="el1"></div>
            <div id="el2"></div>

    2. For partial subtrees, we keep only leaf nodes. e.g., collapsing the range :
        
            <div id="el3"></div>
            <div id="el4">
                <div id="el5">
                    <div id="el6"></div>
                    <!-- el7 is not in the range -->
                </div>
            </div>

        gives :

            <div id="el3"></div>
            <div id="el6"></div>
    """
    pile = element_range[:]
    collapsed: ElementRange = []
    element = pile.pop(0)
    while True:
        # A string or tag encountered here can't belong to a collapsed node, 
        # otherwise it would have been removed from the pile before.
        # Therefore it can be either : 
        # 
        # 1. COMPLETE SUBTREE -> collapse
        # 2. LEAF NODE -> directly add to the collapsed list
        # 3. PARTIAL SUBTREE -> ignore the node and move one level down
        #
        if isinstance(element, Tag):
            # Grab and remove all the descendants of the current element that 
            # are in the pile.
            descendants_in_pile: ElementRange = []
            while pile and _is_parent(element, pile[0]):
                descendants_in_pile.append(pile.pop(0))

            # 1. COMPLETE SUBTREE
            if all(
                descendant in descendants_in_pile
                for descendant in element.descendants
            ):
                collapsed.append(element)
            
            # 2. LEAF NODE
            elif len(descendants_in_pile) == 0:
                collapsed.append(element)

            # 3. PARTIAL SUBTREE
            else:
                pile = descendants_in_pile + pile
        
        # 2. LEAF NODE
        # String at this point can only be a leaf node.
        else:
            collapsed.append(element)

        # Finally move on to next element.
        if pile:
            element = pile.pop(0)
        else:
            break
    return collapsed