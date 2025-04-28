import pathlib
import os
from typing import Optional, Any, Literal, Dict
from pathlib import Path
from tempfile import mkdtemp
import logging

from pydantic import Field, BaseModel

_LOGGER = logging.getLogger(__name__)


APP_ROOT = pathlib.Path(__file__).resolve().parent.parent
TEST_DATA_DIR = APP_ROOT / "test_data"
DEFAULT_ARRETE_TEMPLATE = open(
    APP_ROOT / "arretify" / "templates" / "arrete.html", "r", encoding="utf-8"
).read()
OCR_FILE_EXTENSION = ".md"


class Settings(BaseModel):
    # General settings
    env: Literal["development", "production"] = Field(default="production")
    tmp_dir: Path = Field(default_factory=lambda: Path(mkdtemp(prefix="arretify-")))

    # Settings for clients_api_droit
    legifrance_client_id: Optional[str] = Field(default=None)
    legifrance_client_secret: Optional[str] = Field(default=None)
    eurlex_web_service_username: Optional[str] = Field(default=None)
    eurlex_web_service_password: Optional[str] = Field(default=None)

    @classmethod
    def from_env(cls, env_map: Dict[str, str]) -> "Settings":
        """
        Load settings from environment variables.
        """
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
