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
from dataclasses import replace as dataclass_replace
from typing import Literal

from zeep.exceptions import Error as ZeepError

from arretify._vendor.clients_api_droit.clients_api_droit.eurlex import (
    EurlexClient,
    EurlexSettings,
    search_act,
)
from arretify.errors import ErrorCodes, SettingsError, catch_and_convert_into_arretify_error
from arretify.types import SessionContext
from arretify.utils.dev_cache import use_dev_cache

ActType = Literal["directive", "regulation", "decision"]


def initialize_eurlex_client(session_context: SessionContext) -> SessionContext:
    if (
        not session_context.settings.eurlex_web_service_username
        or not session_context.settings.eurlex_web_service_password
    ):
        raise SettingsError("Eurlex credentials are not provided")

    eurlex_settings = EurlexSettings(
        web_service_username=session_context.settings.eurlex_web_service_username,
        web_service_password=session_context.settings.eurlex_web_service_password,
        tmp_dir=session_context.settings.tmp_dir,
    )
    eurlex_client = EurlexClient(settings=eurlex_settings)
    return dataclass_replace(
        session_context,
        eurlex_client=eurlex_client,
    )


@use_dev_cache
@catch_and_convert_into_arretify_error(ZeepError, ErrorCodes.law_data_api_error)
def get_eu_act_url_with_year_and_num(
    session_context: SessionContext,
    act_type: ActType,
    year: int,
    number: int,
) -> str | None:
    eurlex_client = _assert_client_initialized(session_context)

    for act in search_act(eurlex_client, act_type, year, number):
        return act["url"]
    return None


def _assert_client_initialized(session_context: SessionContext) -> EurlexClient:
    if session_context.eurlex_client is None:
        raise ValueError("Eurlex client is not initialized")
    return session_context.eurlex_client
