from typing import Callable, List, Tuple, Iterator

from bs4 import BeautifulSoup, Tag, PageElement

from .html_tree_navigation import is_parent, is_descendant, closest_common_ancestor


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
        if is_parent(collapsed[-1], current):
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


def _find_next_after(element: PageElement) -> PageElement | None:
    if element.next_sibling:
        return element.next_sibling
    else:
        next_element = element.next_element
        while next_element and is_descendant(next_element, element):
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
        # otherwise it would have been removed from the pile before (step 0.).
        # Therefore it can be either : 
        # 
        # 1. COMPLETE SUBTREE -> collapse
        # 2. LEAF NODE -> directly add to the collapsed list
        # 3. PARTIAL SUBTREE -> ignore the node and move one level down
        #
        if isinstance(element, Tag):
            # 0. Grab and remove all the descendants of the current element that 
            # are in the pile.
            descendants_in_pile: ElementRange = []
            while pile and is_parent(element, pile[0]):
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


def get_contiguous_elements_left(start_tag: Tag) -> List[PageElement]:
    """
    List elements contiguous to `start_tag` in parsing order in the left direction.
    
    Example, with the following html structure :
        <div>
            <div id="blu"></div>
            <div id="bli">
                <span id="bla"></span>
                blo
            </div>
            <div id="start"></div>
        </div>
    
    This function will return the following list of elements :
        [bli, "blo"]
    """
    elements: List[PageElement] = []
    for element_range in iter_collapsed_range_left(start_tag):
        if len(element_range) < 2:
            continue

        elif len(element_range) == 2:
            elements.insert(0, element_range[-2])
            continue

        # If more than 2 elements, the right most neighbor has already been encountered, 
        # so we can ignore that range
        # If in addition, we have reached the contiguous neighbors at the top of ancestor
        # hierarchy, it means we can stop collecting elements.
        common_ancestor = closest_common_ancestor(*element_range[:-1])
        if is_parent(common_ancestor, start_tag):
            break

    return elements


def get_contiguous_elements_right(start_tag: Tag) -> List[PageElement]:
    """
    List elements contiguous to `start_tag` in parsing order in the right direction.

    Example, with the following html structure :
        <div id="start"></div>
        <div id="bli">
            <span id="bla">blo</span>
            blu
        </div>
        <div id="ble"></div>

    This function will return the following list of elements :
        [bli, bla, "blo"]
    """
    elements: List[PageElement] = []
    for element_range in iter_collapsed_range_right(start_tag):
        if len(element_range) < 2:
            continue

        # Since we are searching right, we will start from top element and go down.
        # If we have more than 2 elements in the range (including the start element),
        # it means that we reached bottom and we have all contiguous elements.
        if len(element_range) > 2:
            break
        else:
            elements.append(element_range[1])
    
    return elements