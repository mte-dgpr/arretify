from typing import Callable, List, Tuple

from bs4 import BeautifulSoup, Tag, PageElement


def find_element_range(
    tag: Tag, 
    is_end_element: Callable[[PageElement, List[PageElement]], bool | None]
) -> List[PageElement] | None:
    end_element: PageElement | None = None
    all_elements: List[PageElement] = [tag]
    current = _find_next_after(tag)

    while current:
        if current is None:
            return None

        # With the following example :
        #
        #       <div id="el1"></div>
        #       <div id="el2">
        #           <div id="el3"></div>
        #           <div id="el4"></div>
        #       </div>
        #       <div id="el5"></div>
        # 
        # 1. The last element is a parent of current, e.g., with : 
        #       current=el4 
        #       all_elements=[el1, el2, el3]
        #   we get
        #       collapsed = [el1, el3, el4]
        #
        # 2. The last element is not from the same subtree as current, e.g., with :
        #       current=el5
        #       all_elements=[el1, el2, el3, el4]
        #   we get
        #       collapsed = [el1, el2, el5]
        #
        collapsed = _collapse_element_range(all_elements)
        if _is_parent(collapsed[-1], current):
            collapsed.pop()

        was_found = is_end_element(current, collapsed)
        if was_found is True:
            end_element = current
            break
        elif was_found is None:
            return None

        all_elements.append(current)
        current = current.next_element
    
    if not end_element:
        return None
    
    return _collapse_element_range(all_elements) + [end_element]


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


def _collapse_element_range(element_range: List[PageElement]) -> List[PageElement]:
    pile = element_range[:]
    collapsed: List[PageElement] = []
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
            descendants_in_pile: List[PageElement] = []
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