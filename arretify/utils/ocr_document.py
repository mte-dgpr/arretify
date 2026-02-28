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

OCR_DOCUMENT_JSON_FILE_NAME = "ocr_document.json"


class Page(BaseModel):
    """
    Container for the content of a page after OCR processing.
    Assets are stored as a dictionary mapping asset names to content.
    Content can be None for lazy loading from disk.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    index: int
    """The page index in a document starting from 1"""

    assets: dict[str, str | None] = Field(default_factory=dict)
    """Dictionary mapping asset names to their content (None if not loaded)"""

    dir_path: Path | None = None
    """Directory path for this page's assets (no persisted, used only for lazy loading)"""

    @model_serializer
    def serialize_model(self):
        """Serialize only index and asset names (not content) for JSON storage."""
        return dict(
            index=self.index,
            assets={name: None for name in self.assets.keys()},
        )


class OcrDocument(BaseModel):
    """
    Represents an OCR document containing all pages and document-level metadata.
    """

    ocr_model: str = "mistral-ocr-2512"
    pages: list[Page] = Field(default_factory=list)


def set_asset(page: Page, name: str, content: str | None = None) -> None:
    """
    Set content for an asset.
    This is an in-memory operation - use save_document() to persist to disk.
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
    if page.dir_path is None:
        raise ValueError(f"Cannot load asset '{name}' without dir_path")

    asset_path = page.dir_path / name
    if not asset_path.is_file():
        raise ValueError(f"Asset file not found at {asset_path}")

    asset = asset_path.read_text(encoding="utf-8")
    page.assets[name] = asset
    return asset


def save_ocr_document(ocr_document: OcrDocument, ocr_document_dir: Path) -> None:
    # Save all page assets to their respective directories
    for page in ocr_document.pages:
        page_dir = ocr_document_dir / str(page.index)
        page_dir.mkdir(parents=True, exist_ok=True)

        # Update page's dir_path
        page = page.model_copy(update=dict(dir_path=page_dir))

        # Save all assets with content to disk
        for asset_name, content in page.assets.items():
            if content is not None:
                asset_path = page_dir / asset_name
                with open(asset_path, "w", encoding="utf-8") as f:
                    f.write(content)

    # Save centralized ocr_document.json file
    json_path = ocr_document_dir / OCR_DOCUMENT_JSON_FILE_NAME
    with open(json_path, "w", encoding="utf-8") as f:
        f.write(ocr_document.model_dump_json(indent=2))


def load_ocr_document(ocr_document_dir: Path) -> OcrDocument:
    json_path = ocr_document_dir / OCR_DOCUMENT_JSON_FILE_NAME
    if not json_path.is_file():
        raise ValueError(f"Pages JSON file not found at {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        ocr_document = OcrDocument.model_validate_json(f.read())

    # Set dir_path for each page
    ocr_document.pages = [
        page.model_copy(update=dict(dir_path=ocr_document_dir / str(page.index)))
        for page in ocr_document.pages
    ]
    return ocr_document
