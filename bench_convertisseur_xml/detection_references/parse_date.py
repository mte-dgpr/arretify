import re
import calendar
from datetime import date
from typing import Literal, List, get_args, cast, TypedDict

# Important so that locale is initialized
from ..settings import *
from .text_utils import remove_accents


MONTH_NAMES = list([remove_accents(m) for m in calendar.month_name])

MONTH_NAMES_RE = '|'.join(MONTH_NAMES[1:])
DATE1_RE = r'((?P<day_first>1er)|(?P<day>\d{1,2})) (?P<month_name>' + MONTH_NAMES_RE + r') ((?P<year>\d{4})|(?P<year_2digits>\d{2}))(\s|\.|$|,|\)|;)'
DATE2_RE = r'(?P<day>\d{2})/(?P<month>\d{2})/((?P<year>\d{4})|(?P<year_2digits>\d{2}))(\s|\.|$|,|\)|;)'
DATE_RES = [
    DATE1_RE,
    DATE2_RE,
]


class DateMatchDict(TypedDict):
    day_first: str
    day: str
    month_name: str
    year: str
    month: str
    year_2digits: str


def parse_date(match_dict: DateMatchDict) -> date | None:
    if match_dict.get('month_name'):
        match_month = match_dict['month_name'].lower()
        month = None
        for i, month_name in enumerate(MONTH_NAMES):
            if month_name.startswith(match_month):
                month = i
        if month is None:
            raise RuntimeError(f'couldnt find month for "{match_month}"')
    elif match_dict.get('month'):
        month = int(match_dict['month'])
    else:
        return None
    
    if match_dict.get('day_first'):
        day = 1
    elif match_dict.get('day'):
        day = int(match_dict['day'])
    else:
        return None

    if match_dict.get('year_2digits'):
        year_2digits = int(match_dict['year_2digits'])
        year = year_2digits + (1900 if year_2digits > (date.today().year - 2000 + 5) else 2000)
    elif match_dict.get('year'):
        year = int(match_dict['year'])
    else:
        return None

    return date(
        day=day,
        month=month,
        year=year,
    )
