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
import logging
import os
import pathlib
from pathlib import Path
from tempfile import mkdtemp
from typing import Any, Dict, Literal, Optional, Type, TypeVar

from pydantic import BaseModel, Field

SettingsType = TypeVar("SettingsType", bound="Settings")


_LOGGER = logging.getLogger(__name__)
_SETTINGS_ENV_MAP = {
    # General settings
    "tmp_dir": "TMP_DIR",
    "env": "ENV",
    # Settings for clients_api_droit
    "legifrance_client_id": "LEGIFRANCE_CLIENT_ID",
    "legifrance_client_secret": "LEGIFRANCE_CLIENT_SECRET",
    "eurlex_web_service_username": "EURLEX_WEB_SERVICE_USERNAME",
    "eurlex_web_service_password": "EURLEX_WEB_SERVICE_PASSWORD",
    # Settings for MistralAI
    "mistral_api_key": "MISTRAL_API_KEY",
    "mistral_ocr_model": "MISTRAL_OCR_MODEL",
}


# Static settings
APP_ROOT = pathlib.Path(__file__).resolve().parent.parent
EXAMPLES_DIR = APP_ROOT / "examples"
DEFAULT_ARRETE_TEMPLATE = open(
    APP_ROOT / "arretify" / "templates" / "arrete.html", "r", encoding="utf-8"
).read()
OCR_FILE_EXTENSION = ".md"


class Settings(BaseModel):
    # General settings
    env: Literal["development", "production"] = Field(default="production")
    tmp_dir: Path = Field(default_factory=lambda: Path(mkdtemp(prefix="arretify-")))

    # Settings for clients_api_droit
    legifrance_client_id: Optional[str] = Field(
        default=None,
        description=(
            "Client ID for Legifrance API. " "If not set, the client will not be initialized."
        ),
    )
    legifrance_client_secret: Optional[str] = Field(
        default=None,
        description=(
            "Client secret for Legifrance API. " "If not set, the client will not be initialized."
        ),
    )
    eurlex_web_service_username: Optional[str] = Field(
        default=None,
        description=(
            "Username for Eurlex web service. " "If not set, the client will not be initialized."
        ),
    )
    eurlex_web_service_password: Optional[str] = Field(
        default=None,
        description=(
            "Password for Eurlex web service. " "If not set, the client will not be initialized."
        ),
    )

    # Settings for MistralAI
    mistral_api_key: Optional[str] = Field(
        default=None,
        description=(
            "API key for Mistral AI. " "If not set, the Mistral client will not be initialized."
        ),
    )
    mistral_ocr_model: str = Field(
        default="mistral-ocr-2503",
        description="Mistral OCR model to use for processing documents.",
    )

    @classmethod
    def from_env(cls: Type[SettingsType], env_map: Dict[str, str] | None = None) -> SettingsType:
        """
        Load settings from environment variables.
        """
        if env_map is None:
            env_map = _SETTINGS_ENV_MAP

        # Remove keys with None values, so pydantic will use field defaults
        clean_values = {
            field: os.getenv(env_var)
            for field, env_var in env_map.items()
            if os.getenv(env_var) is not None
        }
        return cls(**clean_values)

    def model_post_init(self, _: Any) -> None:
        # Pretty print the current settings
        _LOGGER.debug(f"Settings initialized: {self.model_dump_json(indent=2)}")

        if not self.tmp_dir.exists():
            self.tmp_dir.mkdir(parents=True, exist_ok=True)
