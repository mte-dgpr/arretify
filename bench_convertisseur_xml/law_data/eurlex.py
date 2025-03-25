from typing import Literal

# Load settings to be sure that we provide 
# config to the eurlex package
from bench_convertisseur_xml.settings import LOGGER
from clients_api_droit.eurlex import search_act

from .dev_cache import use_dev_cache


ActType = Literal['directive', 'regulation', 'decision']


@use_dev_cache
def get_eu_act_url_with_year_and_num(act_type: ActType, year: int, number: int) -> str | None:
    for act in search_act(act_type, year, number):
        return act['url']
    return None