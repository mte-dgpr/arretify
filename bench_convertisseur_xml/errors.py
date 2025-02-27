from typing import Union
from enum import Enum

from .types import LineColumn


class ErrorCodes(Enum):
    markdown_parsing='markdown_parsing'
    unbalanced_quote='unbalanced_quote'
    non_contiguous_sections='non_contiguous_sections'


class ParsingError(BaseException):
    
    def __init__(self, code: ErrorCodes, line_col: LineColumn, msg: Union[str, None]=None):
        complete_msg = f'[line: {line_col[0] + 1}, col: {line_col[1] + 1}] {msg or code.value}'
        super(ParsingError, self).__init__(complete_msg)