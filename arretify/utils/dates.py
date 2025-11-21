#
# Copyright (c) 2025 Direction générale de la prévention des risques (DGPR).
#
# This file is part of Arrêtify.
# See https://github.com/mte-dgpr/arretify for further info.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from datetime import date, datetime

DATE_FORMAT = "%Y-%m-%d"
DATE_STR_LENGTH = len(date.today().strftime(DATE_FORMAT))


def render_year_str(year: int) -> str:
    year_str = str(year)
    if len(year_str) != 4:
        raise ValueError(f"Invalid year {year}")
    return year_str


def parse_year_str(year_str: str) -> int:
    if len(year_str) == 4:
        return int(year_str)
    if len(year_str) == 2:
        return int(year_str) + (1900 if int(year_str) > (date.today().year - 2000 + 5) else 2000)
    else:
        raise ValueError(f"Invalid year string {year_str}")


def render_date_str(date_object: date) -> str:
    return date_object.strftime(DATE_FORMAT)


def parse_date_str(date_str: str) -> date:
    return datetime.strptime(date_str, DATE_FORMAT).date()
