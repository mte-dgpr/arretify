from typing import Union
from enum import Enum

class ErrorCodes(Enum):
    markdown_parsing='markdown_parsing'
    unbalanced_quote='unbalanced_quote'


class ParsingError(BaseException):
    
    def __init__(self, code: ErrorCodes, msg: Union[str, None]=None):
        super(ParsingError, self).__init__(msg or code.value)