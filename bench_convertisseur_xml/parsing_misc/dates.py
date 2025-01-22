import re
import calendar
from datetime import date, datetime
from typing import Literal, List, get_args, cast, TypedDict, Pattern
from bs4 import BeautifulSoup

# Important so that locale is initialized
from bench_convertisseur_xml.settings import *
from bench_convertisseur_xml.html_schemas import DATE_SCHEMA
from bench_convertisseur_xml.utils.html import make_data_tag

DATE_FORMAT = '%Y-%m-%d'

MONTH_NAMES = list(calendar.month_name)

# Check that the date string is followed by a valid separator
# so that we don't match strings like 54/67/1980/A.
LOOKAHEAD_RES = r'(?=\s|\.|$|,|\)|;)'
MONTH_NAMES_RES = '|'.join(MONTH_NAMES[1:])
DATE1_RES = r'(((?P<day_first>1er)|(?P<day>\d{1,2})) (?P<month_name>' + MONTH_NAMES_RES + r') ((?P<year>\d{4})|(?P<year_2digits>\d{2})))' + LOOKAHEAD_RES
DATE2_RES = r'((?P<day>\d{2})/(?P<month>\d{2})/((?P<year>\d{4})|(?P<year_2digits>\d{2})))' + LOOKAHEAD_RES
DATE_RE_LIST = [ re.compile(DATE1_RES), re.compile(DATE2_RES) ]


class DateMatchDict(TypedDict):
    day_first: str
    day: str
    month_name: str
    year: str
    month: str
    year_2digits: str


def handle_date_match_groupdict(match_dict: DateMatchDict) -> date | None:
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


def parse_date(string: str) -> date | None:
    for date_re in DATE_RE_LIST:
        match = date_re.search(string)
        if not match:
            continue
        return handle_date_match_groupdict(cast(DateMatchDict, match.groupdict()))
    return None


def render_date_attribute(date_object: date) -> str:
    return date_object.strftime(DATE_FORMAT)


def parse_date_attribute(date_str: str) -> date:
    return datetime.strptime(date_str, DATE_FORMAT).date()


def make_date_element(soup: BeautifulSoup, date_str: str, date_object: date):
    date_container = make_data_tag(soup, DATE_SCHEMA)
    date_container.string = date_str
    date_container['datetime'] = render_date_attribute(date_object)
    return date_container