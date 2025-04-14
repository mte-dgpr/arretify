import csv
import os
from optparse import OptionParser
from pathlib import Path
from typing import Dict

import requests


UNCATCHED_FILE_TYPES = [
    "rapport",
    "document de procédure",
    "fiche seveso",
    "inspection",
    "rapport d'ap d'autorisation",
]


CATCHED_FILE_TYPES_CONVERTER = {
    "ap d'autorisation": "AP",
    "ap enregistrement": "AP",
    "ap autorisation temporaire": "AP",
    "arrêté préfectoral": "AP",
    "ap servitude d'utilité publique": "AP",
    "ap prescriptions complémentaires": "APC",
    "arrêté de mise en demeure": "APMD",
    "ap mise en demeure": "APMD",
    "ap levée de mise en demeure": "APMD",
    "ap mesures d'urgence": "APMU",
    "autre": "Autre",
}


def get_icpe_data(code_aiot: str) -> Dict:

    url = f"https://georisques.gouv.fr/api/v1/installations_classees?codeAIOT={code_aiot}"
    response = requests.get(url, headers={"accept": "application/json"})

    if response.status_code != 200:
        raise requests.HTTPError(response=response)

    icpe_data = response.json()
    if icpe_data.get("results", 0) == 0:
        return {}

    return icpe_data["data"][0]


def process_icpe_data(icpe_data: Dict, code_aiot: str, out_dir: Path):

    icpe_documents = icpe_data.get("documentsHorsInspection", [])
    if not icpe_documents:
        print(f"No document found for ICPE {code_aiot}")

    icpe_dir = out_dir / code_aiot
    if not icpe_dir.is_dir():
        os.mkdir(icpe_dir)

    for document_data in icpe_documents:

        file_type = document_data["typeFichier"].lower()
        if file_type in UNCATCHED_FILE_TYPES:
            print(f"File type '{file_type}' not catched, continue...")
            continue

        try:
            file_type_save = CATCHED_FILE_TYPES_CONVERTER[file_type]
        except KeyError:
            err_msg = (
                f"Unknown file type '{file_type}', please specify if it should be catched or not"
            )
            raise KeyError(err_msg)

        file_name = f"{document_data['dateFichier']}_{file_type_save}.pdf"
        file_path = icpe_dir / file_name
        if file_path.is_file():
            print(f"File {file_name} already exists, continue...")
            continue

        response = requests.get(document_data["urlFichier"], stream=True)

        if response.status_code == 500:
            print(f"File {file_name} not existing on server side, continue...")
            continue

        with open(file_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Downloaded file {file_name}")


def download_one_icpe(code_aiot: str, out_dir: Path):

    try:
        icpe_data = get_icpe_data(code_aiot)
    except requests.HTTPError as err:
        print(f"Failed to get ICPE {code_aiot} from georisques")
        print(err)

    process_icpe_data(icpe_data, code_aiot, out_dir)


def iter_icpe_file(file_path: Path):
    with open(file_path, "r", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile, delimiter=";")
        for icpe_dict in reader:
            yield icpe_dict


def main(icpe_file: Path, out_dir: Path, only_complete: bool = True):

    if not out_dir.is_dir():
        os.mkdir(out_dir)

    for icpe_dict in iter_icpe_file(icpe_file):

        has_all_aps = icpe_dict["AP complets ? Oui "].lower().strip() == "oui"

        if only_complete and has_all_aps:

            code_aiot = icpe_dict["\ufeffCode AIOT"]
            print(f"--- ICPE {code_aiot}")
            download_one_icpe(code_aiot, out_dir)


if __name__ == "__main__":

    parser = OptionParser()

    parser.add_option("--limit", default=None, type="int")
    parser.add_option(
        "-i",
        "--icpe-file",
        default="tmp/20240813_permis_consolidés_état_des_lieux_MAJ_27_aout_2024 annoté.csv",
    )
    parser.add_option("-o", "--out-dir", default="tmp/AP-georisques")

    (options, args) = parser.parse_args()

    icpe_file = Path(options.icpe_file)
    out_dir = Path(options.out_dir)

    main(icpe_file, out_dir)
