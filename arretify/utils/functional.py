from typing import Iterable, Iterator, Union, Callable, TypeVar


P = TypeVar("P")


def flat_map_string(
    elements: Iterable[Union[P, str]],
    map_func: Callable[[str], Iterable[P | str]],
) -> Iterator[P | str]:
    """
    Example:
        >>> elements = ["string", 2, "another", 3]
        >>> def map_func(x): return [x.upper()]
        >>> list(flat_map_string(elements, map_func))
        ['STRING', 2, 'ANOTHER', 3]
    """
    for element in elements:
        if isinstance(element, str):
            yield from map_func(element)
        else:
            yield element
