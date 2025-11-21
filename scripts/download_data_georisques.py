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
import csv
import logging
import os
import time
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from optparse import OptionParser
from pathlib import Path

import requests

_LOGGER = logging.getLogger(__name__)


CATCHED_FILE_TYPES = [
    # Should be the arretes we are looking for, however some might be wrongly classified
    "ap d'autorisation",
    "ap enregistrement",
    "arrêté préfectoral",
    "ap servitude d'utilité publique",
    "ap prescriptions complémentaires",
    # Should not be the arretes we are looking for, however some might be wrongly classified
    "rapport",
    "document de procédure",
    "fiche seveso",
    "inspection",
    "rapport d'ap d'autorisation",
    "arrêté de mise en demeure",
    "ap mise en demeure",
    "ap levée de mise en demeure",
    "ap mesures conservatoires",
    "ap autorisation temporaire",
    "ap mesures d'urgence",
    # For these we do not know beforehand
    "autre",
]


@dataclass
class FileMetadata:
    code_aiot: str
    date: str
    type: str
    name: str
    written_on_disk: bool


def _group_by_key(items, key_func):
    grouped = defaultdict(list)
    for item in items:
        key = key_func(item)
        grouped[key].append(item)
    return dict(grouped)


def get_icpe_data(code_aiot: str) -> dict:

    url = f"https://georisques.gouv.fr/api/v1/installations_classees?codeAIOT={code_aiot}"

    response = requests.get(url, headers={"accept": "application/json"})

    if response.status_code != 200:
        raise requests.HTTPError(response=response)

    icpe_data = response.json()
    if icpe_data.get("results", 0) == 0:
        return {}

    return icpe_data["data"][0]


def process_icpe_data(
    icpe_data: dict,
    code_aiot: str,
    files_list: list[FileMetadata],
    out_dir: Path,
    sleep_time: float = 0.5,
    dry_run: bool = False,
):

    icpe_documents = icpe_data.get("documentsHorsInspection", [])
    if not icpe_documents:
        _LOGGER.warning(f"No document found for ICPE {code_aiot}")

    for document_data in icpe_documents:

        file_date = document_data["dateFichier"]

        file_type = document_data["typeFichier"].lower()
        if file_type not in CATCHED_FILE_TYPES:
            err_msg = (
                f"Unknown file type '{file_type}', please specify if it should be catched or not"
            )
            raise KeyError(err_msg)

        # Write filename for reporting
        file_name = document_data["nomFichier"]
        file_name = file_name.replace("/", "-")  # avoid issues with paths
        file_name = file_name.replace("*", "")  # avoid issues with paths
        # We use "'" to avoid issues when reading AIOT codes starting with zeroes
        file_aiot = f"'{code_aiot}"
        written_on_disk = False

        # Check if exists on disk
        file_name_save = f"{file_date}_{file_type}_{file_name}.pdf"

        icpe_dir = out_dir / code_aiot
        file_path = icpe_dir / file_name_save

        if file_path.is_file():
            _LOGGER.info(f"File {file_name_save} already exists, continue...")
            written_on_disk = True
            files_list.append(
                FileMetadata(file_aiot, file_date, file_type, file_name, written_on_disk)
            )
            continue

        # Do not download if dry run
        if dry_run:
            _LOGGER.info(f"Seen file {file_name_save}")
            files_list.append(
                FileMetadata(file_aiot, file_date, file_type, file_name, written_on_disk)
            )
            continue

        # Download file
        response = requests.get(document_data["urlFichier"], stream=True)

        if response.status_code != 200:
            _LOGGER.warning(
                f"Failed downloading {file_name_save} with HTTP status {response.status_code}"
                " continue..."
            )
            files_list.append(
                FileMetadata(file_aiot, file_date, file_type, file_name, written_on_disk)
            )
            time.sleep(sleep_time)  # avoid error 503
            continue

        # Save file
        if not out_dir.is_dir():
            os.mkdir(out_dir)

        if not icpe_dir.is_dir():
            os.mkdir(icpe_dir)

        with open(file_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        _LOGGER.info(f"Downloaded file {file_name_save}")
        written_on_disk = True
        files_list.append(FileMetadata(file_aiot, file_date, file_type, file_name, written_on_disk))
        time.sleep(sleep_time)  # avoid error 503

    return files_list


def download_one_icpe(
    code_aiot: str, files_list: list[FileMetadata], out_dir: Path, dry_run: bool = False
):

    try:
        icpe_data = get_icpe_data(code_aiot)
    except requests.HTTPError as err:
        _LOGGER.warning(f"Failed to get ICPE {code_aiot} from georisques")
        _LOGGER.warning(err)

    process_icpe_data(icpe_data, code_aiot, files_list, out_dir, dry_run=dry_run)


def iter_icpe_file(file_path: Path):
    with open(file_path, "r", encoding="utf-8") as file:
        for line in file:
            yield line.strip()


def initialize_logger():

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter("%(levelname)s - %(message)s"))
    handlers: list[logging.StreamHandler] = [stream_handler]
    logging.basicConfig(level=logging.INFO, handlers=handlers)


def main(icpe_file: Path, out_dir: Path, dry_run: bool = False, report: bool = True):
    """Run downloading of ICPE documents from georisques.gouv.fr

    Args:
        icpe_file (Path): Path to a file containing one ICPE code AIOT per line
        out_dir (Path): Dir where to save downloaded files, if None files are not saved
        dry_run (bool, optional): If True, do not download files, only list them.
        report (bool, optional): If True, generate a CSV report of downloaded files.
    """
    initialize_logger()

    files_list: list[FileMetadata] = []

    for code_aiot in iter_icpe_file(icpe_file):
        _LOGGER.info(f"--- ICPE {code_aiot}")
        download_one_icpe(code_aiot, files_list, out_dir, dry_run=dry_run)

    _LOGGER.info("--- Summary ---")
    files_by_type = _group_by_key(files_list, lambda f: f.type)
    for file_type, files_type_list in files_by_type.items():
        _LOGGER.info(f"Seen or downloaded {len(files_type_list)} files of type '{file_type}'")

    if report:
        file_list_name = out_dir / f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_report.csv"
        with open(file_list_name, mode="w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(["Code AIOT", "dateFichier", "typeFichier", "nomFichier", "Enregistré"])
            for file_meta in files_list:
                writer.writerow(
                    [
                        file_meta.code_aiot,
                        file_meta.date,
                        file_meta.type,
                        file_meta.name,
                        file_meta.written_on_disk,
                    ]
                )


if __name__ == "__main__":

    parser = OptionParser()

    parser.add_option(
        "-i",
        "--icpe-file",
    )
    parser.add_option(
        "-o",
        "--out-dir",
    )
    parser.add_option(
        "--dry-run",
        action="store_true",
        default=False,
    )
    parser.add_option(
        "--report",
        action="store_true",
        default=True,
    )
    (options, args) = parser.parse_args()

    icpe_file = Path(options.icpe_file)
    out_dir = Path(options.out_dir)
    dry_run = options.dry_run
    report = options.report

    main(icpe_file, out_dir, dry_run=dry_run, report=report)
