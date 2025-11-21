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

# TODO : group with eurlex and legifrance clients to a new folder
# containing all integrations with external APIs.
from dataclasses import replace as dataclass_replace

from arretify._vendor import mistralai
from arretify.errors import DependencyError, SettingsError
from arretify.types import SessionContext


def initialize_mistral_client(session_context: SessionContext) -> SessionContext:
    if not hasattr(mistralai, "Mistral"):
        raise DependencyError("Dependency mistralai seems to be missing")

    if not session_context.settings.mistral_api_key:
        raise SettingsError("MistralAI credentials are not provided")

    mistral_client = mistralai.Mistral(api_key=session_context.settings.mistral_api_key)
    return dataclass_replace(
        session_context,
        mistral_client=mistral_client,
    )
