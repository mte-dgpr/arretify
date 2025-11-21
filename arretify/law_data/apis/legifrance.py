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
from datetime import date

from requests.exceptions import RequestException

from arretify._vendor.clients_api_droit.clients_api_droit.legifrance import (
    LegifranceClient,
    LegifranceSettings,
    authenticate,
    search_arrete,
    search_circulaire,
    search_decret,
)
from arretify.errors import ErrorCodes, SettingsError, catch_and_convert_into_arretify_error
from arretify.types import SessionContext
from arretify.utils.dev_cache import use_dev_cache


@catch_and_convert_into_arretify_error(RequestException, ErrorCodes.law_data_api_error)
def initialize_legifrance_client(session_context: SessionContext) -> SessionContext:
    if (
        not session_context.settings.legifrance_client_id
        or not session_context.settings.legifrance_client_secret
    ):
        raise SettingsError("Legifrance credentials are not provided")

    legifrance_settings = LegifranceSettings(
        client_id=session_context.settings.legifrance_client_id,
        client_secret=session_context.settings.legifrance_client_secret,
        tmp_dir=session_context.settings.tmp_dir,
    )
    legifrance_client = authenticate(LegifranceClient(settings=legifrance_settings))
    return dataclass_replace(
        session_context,
        legifrance_client=legifrance_client,
    )


@use_dev_cache
@catch_and_convert_into_arretify_error(RequestException, ErrorCodes.law_data_api_error)
def get_arrete_legifrance_id(session_context: SessionContext, date: date, title: str) -> str | None:
    legifrance_client = _assert_client_initialized(session_context)
    for arrete in search_arrete(legifrance_client, date, title):
        arrete_cid = arrete["titles"][0]["cid"]
        return arrete_cid
    return None


@use_dev_cache
@catch_and_convert_into_arretify_error(RequestException, ErrorCodes.law_data_api_error)
def get_decret_legifrance_id(
    session_context: SessionContext, date: date, num: str | None, title: str | None
) -> str | None:
    if not num and not title:
        raise ValueError("Either num or title must be provided")

    legifrance_client = _assert_client_initialized(session_context)
    for decret in search_decret(legifrance_client, date, num=num, title=title):
        decret_cid = decret["titles"][0]["cid"]
        return decret_cid
    return None


@use_dev_cache
@catch_and_convert_into_arretify_error(RequestException, ErrorCodes.law_data_api_error)
def get_circulaire_legifrance_id(
    session_context: SessionContext, date: date, title: str
) -> str | None:
    legifrance_client = _assert_client_initialized(session_context)
    for circulaire in search_circulaire(legifrance_client, date, title):
        circulaire_cid = circulaire["titles"][0]["cid"]
        return circulaire_cid
    return None


def _assert_client_initialized(session_context: SessionContext) -> LegifranceClient:
    if not session_context.legifrance_client:
        raise ValueError("Legifrance client is not initialized")
    return session_context.legifrance_client
