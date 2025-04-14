import re
from typing import Iterator, Union, Iterable, Dict
from dataclasses import replace as dataclass_replace

from .types import PatternString, Settings
from .helpers import (
    normalize_string,
)


MatchFlow = Iterable[Union[str, "MatchProxy"]]


class PatternProxy:
    """
    A proxy class for regex patterns with additional settings.

    >>> pattern_proxy = PatternProxy(r'cafe', Settings(ignore_accents=True))
    >>> match = pattern_proxy.match("café")
    >>> if match:
    ...     print(match.group(0))
    ... else:
    ...     print("No match")
    café
    """

    def __init__(
        self,
        pattern_string: PatternString,
        settings: Settings | None = None,
    ):
        self.pattern_string = pattern_string
        self.settings = settings or Settings()
        # Regex handle case insensitivity natively, so we don't need to include it
        # in string normalization settings.
        self._settings_for_normalization = dataclass_replace(self.settings, ignore_case=False)

        pattern_string_for_compilation = normalize_string(
            pattern_string, self._settings_for_normalization
        )
        compile_flags = 0
        if self.settings.ignore_case:
            compile_flags |= re.IGNORECASE

        self._pattern = re.compile(pattern_string_for_compilation, compile_flags)

    def __getattr__(self, attr):
        value = getattr(self._pattern, attr)
        if callable(value):
            raise NotImplementedError(
                f"Function {attr} of re.Pattern is not implemented in PatternProxy"
            )
        return value

    def match(self, string: str) -> Union["MatchProxy", None]:
        match = self._pattern.match(normalize_string(string, self._settings_for_normalization))
        if match:
            return MatchProxy(string, match)
        else:
            return None

    def search(self, string: str) -> Union["MatchProxy", None]:
        match = self._pattern.search(normalize_string(string, self._settings_for_normalization))
        if match:
            return MatchProxy(string, match)
        else:
            return None

    def finditer(self, string: str) -> Iterator["MatchProxy"]:
        for match in self._pattern.finditer(
            normalize_string(string, self._settings_for_normalization)
        ):
            yield MatchProxy(string, match)

    def sub(self, repl: str, string: str) -> str:
        while True:
            match = self._pattern.search(normalize_string(string, self._settings_for_normalization))
            if match:
                string = string[: match.start()] + repl + string[match.end() :]
            else:
                return string


class MatchProxy:
    def __init__(self, string: str, match: re.Match):
        self.string = string
        self.match = match

    def group(self, group: int | str) -> Union[str, None]:
        group_start = self.match.start(group)
        if group_start == -1:
            return None
        return self.string[group_start : self.match.end(group)]

    def groupdict(self) -> Dict[str, Union[str, None]]:
        raw_groupdict = self.match.groupdict()
        return {key: self.group(key) for key in raw_groupdict.keys()}

    def __getattr__(self, attr):
        return getattr(self.match, attr)


def safe_group(match: re.Match | MatchProxy, index: int | str) -> str:
    group_text = match.group(index)
    if group_text is None:
        raise RuntimeError(f"Group {index} not found in match")
    return group_text
