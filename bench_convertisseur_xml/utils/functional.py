from typing import Iterable, Iterator, Union, Callable, TypeVar, Any, cast, Generic, TypeVarTuple

from bench_convertisseur_xml.types import PageElementOrString

# Define generic types
P = TypeVar('P')
Q = TypeVar('Q')
Ts = TypeVarTuple("Ts")

class Lambda(Generic[*Ts]):
    @classmethod
    def cast(cls, f: Callable[[*Ts], P]) -> Callable[[*Ts], P]:
        return f


def flat_map_non_string(
    elements: Iterable[Union[P, str]], 
    map_func: Callable[[P], Iterable[Q | str]]
) -> Iterator[Q | str]:
    '''
    Example:
        >>> elements = ["string", 2, "another", 3]
        >>> def map_func(x): return [x * 2]
        >>> list(flat_map_non_string(elements, map_func))
        ['string', 4, 'another', 6]
    '''
    for element in elements:
        if isinstance(element, str):
            yield element
        else:
            yield from map_func(element)


def flat_map_string(
    elements: Iterable[Union[P, str]], 
    map_func: Callable[[str], Iterable[P | str]]
) -> Iterator[P | str]:
    '''
    Example:
        >>> elements = ["string", 2, "another", 3]
        >>> def map_func(x): return [x.upper()]
        >>> list(flat_map_string(elements, map_func))
        ['STRING', 2, 'ANOTHER', 3]
    '''
    for element in elements:
        if isinstance(element, str):
            yield from map_func(element)
        else:
            yield element