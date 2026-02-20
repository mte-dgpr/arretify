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
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, model_serializer

PAGE_JSON_FILE_NAME = "page.json"


class Page(BaseModel):
    """
    Container for the content of a page after OCR processing.
    Assets are stored as a dictionary mapping asset names to content.
    Content can be None for lazy loading from disk.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    index: int
    """The page index in a document starting from 1"""

    dir_path: Path | None = None
    """Directory path where the page assets are stored on disk"""

    assets: dict[str, str | None] = Field(default_factory=dict)
    """Dictionary mapping asset names to their content (None if not loaded)"""

    @model_serializer
    def serialize_model(self):
        """Serialize only index and asset names (not content) for JSON storage."""
        return dict(index=self.index, assets={name: None for name in self.assets.keys()})


def create_asset(page: Page, name: str, content: str | None = None) -> None:
    """
    Create a new asset with the given name and optional content.
    This is an in-memory operation - use save_page() to persist to disk.
    """
    page.assets[name] = content


def set_asset(page: Page, name: str, content: str) -> None:
    """
    Set content for an asset.
    This is an in-memory operation - use save_page() to persist to disk.
    """
    page.assets[name] = content


def get_or_load_asset(page: Page, name: str) -> str:
    """
    Get asset content, loading from disk if necessary.
    Raises KeyError if asset doesn't exist, ValueError if content can't be loaded.
    """
    if name not in page.assets:
        raise KeyError(f"Asset '{name}' not found in page {page.index}")

    content = page.assets[name]
    if isinstance(content, str):
        return content

    # Content is None, attempt to load from disk
    else:
        if page.dir_path is None:
            raise ValueError(f"Cannot load asset '{name}' without dir_path")

        asset_path = page.dir_path / name
        if not asset_path.is_file():
            raise ValueError(f"Asset file not found at {asset_path}")

        with open(asset_path, "r", encoding="utf-8") as f:
            loaded = f.read()
        page.assets[name] = loaded
        return loaded


def save_page(page: Page) -> None:
    if page.dir_path is None:
        raise ValueError("Cannot save page without dir_path")
    page.dir_path.mkdir(parents=True, exist_ok=True)

    # Save all assets with content to disk
    for asset_name, content in page.assets.items():
        if content is not None:
            asset_path = page.dir_path / asset_name
            with open(asset_path, "w", encoding="utf-8") as f:
                f.write(content)

    # Save JSON file
    page_json_path = page.dir_path / PAGE_JSON_FILE_NAME
    with open(page_json_path, "w", encoding="utf-8") as f:
        f.write(page.model_dump_json(indent=2))


def load_page(page_dir: Path) -> Page:
    page_json_path = page_dir / PAGE_JSON_FILE_NAME
    if not page_json_path.is_file():
        raise ValueError(f"Page JSON file not found at {page_json_path}")

    with open(page_json_path, "r", encoding="utf-8") as f:
        page_json_content = f.read()

    page = Page.model_validate_json(page_json_content)
    return page.model_copy(update=dict(dir_path=page_dir))
