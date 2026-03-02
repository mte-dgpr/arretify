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


class Asset(BaseModel):
    """
    Represents an asset with a name, path, and content.
    Name and path are immutable after creation.
    Content is mutable to allow lazy loading from disk.
    """

    model_config = ConfigDict(extra="forbid")

    name: str = Field(frozen=True)
    path: Path | None = Field(default=None, frozen=True)
    content: str | None = None

    @model_serializer
    def serialize_model(self):
        return dict(
            name=self.name,
        )


class Page(BaseModel):
    """
    Container for the content of a page after OCR processing.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    index: int
    """The page index in a document starting from 1"""

    assets: dict[str, Asset] = Field(default_factory=dict)
    """Assets can be markdown content, images, or other files related to the page."""


class OcrDocument(BaseModel):
    """
    Represents a document after OCR processing, containing all pages and document-level metadata.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    ocr_model: str = "mistral-ocr-2512"
    pages: list[Page] = Field(default_factory=list)


def create_asset(page: Page, name: str, content: str | None = None) -> None:
    """
    Add a new asset to the page.
    Raises an error if asset with the same name already exists.
    This is an in-memory operation - use save_ocr_document() to persist to disk.
    """
    if name in page.assets:
        raise ValueError(f"Asset '{name}' already exists in page {page.index}")
    page.assets[name] = Asset(name=name, content=content)


def get_or_load_asset_content(asset: Asset) -> str:
    """
    Get asset content, loading from disk if necessary.
    Raises ValueError if content can't be loaded.
    Only uses Asset.path for loading.
    """
    if isinstance(asset.content, str):
        return asset.content

    # Content is None, attempt to load from disk
    if asset.path is None:
        raise ValueError(f"Cannot load asset '{asset.name}' without asset.path set")
    asset_path = asset.path

    if not asset_path.is_file():
        raise ValueError(f"Asset file not found at {asset_path}")

    asset.content = asset_path.read_text(encoding="utf-8")
    return asset.content


def save_ocr_document(ocr_document: OcrDocument, ocr_document_dir: Path) -> None:
    for page in ocr_document.pages:
        page_dir = _get_page_dir(ocr_document_dir, page)
        page_dir.mkdir(parents=True, exist_ok=True)

        for asset_name, asset in list(page.assets.items()):
            if asset.content is None:
                continue
            asset = _assign_asset_path(page, asset_name, page_dir)
            assert asset.path is not None
            assert asset.content is not None
            asset.path.write_text(asset.content, encoding="utf-8")

    json_path = ocr_document_dir / OCR_DOCUMENT_JSON_FILE_NAME
    json_path.write_text(ocr_document.model_dump_json(indent=2), encoding="utf-8")


def load_ocr_document(ocr_document_dir: Path) -> OcrDocument:
    json_path = ocr_document_dir / OCR_DOCUMENT_JSON_FILE_NAME
    if not json_path.is_file():
        raise ValueError(f"Pages JSON file not found at {json_path}")

    ocr_document = OcrDocument.model_validate_json(json_path.read_text(encoding="utf-8"))

    for page in ocr_document.pages:
        page_dir = _get_page_dir(ocr_document_dir, page)
        for asset_name in list(page.assets):
            _assign_asset_path(page, asset_name, page_dir)
    return ocr_document


def _get_page_dir(ocr_document_dir: Path, page: Page) -> Path:
    return ocr_document_dir / str(page.index)


def _assign_asset_path(page: Page, asset_name: str, page_dir: Path) -> Asset:
    """Compute the asset path and update the asset in the page in-place."""
    asset_path = page_dir / asset_name
    page.assets[asset_name] = page.assets[asset_name].model_copy(
        update=dict(name=asset_name, path=asset_path)
    )
    return page.assets[asset_name]
