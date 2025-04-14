from typing import Iterator, Iterable

from arretify.types import PageElementOrString


def merge_strings(
    str_or_element_gen: Iterable[PageElementOrString],
) -> Iterator[PageElementOrString]:
    """
    Example:
        >>> elements = ["Hello-", "world!", Tag(name="p"), "More text"]
        >>> list(merge_strings(elements))
        ['Hello-world!', <p></p>, 'More text']
    """
    accumulator: str | None = None
    for str_or_element in str_or_element_gen:
        if isinstance(str_or_element, str):
            accumulator = (accumulator or "") + str_or_element
        else:
            if accumulator is not None:
                yield accumulator
            accumulator = None
            yield str_or_element
    if accumulator is not None:
        yield accumulator
