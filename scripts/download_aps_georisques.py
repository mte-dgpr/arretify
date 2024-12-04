import csv
import os
from pathlib import Path

import requests


def get_icpe(codeAIOT: str):
    url = f'https://georisques.gouv.fr/api/v1/installations_classees?codeAIOT={codeAIOT}'
    response = requests.get(url, headers={ 'accept': 'application/json' })

    if response.status_code != 200:
        raise requests.HTTPError(response=response)

    paginated_data = response.json()
    if paginated_data.get('results', 0) == 0:
        raise requests.HTTPError("No result")

    return paginated_data['data'][0]


def iter_ieds(file_path: Path):
    with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')
        for ied_dict in reader:
            yield ied_dict


def main(ied_file: Path, out_dir: Path):
    if not out_dir.is_dir():
        os.mkdir(out_dir)    
    for ied_dict in iter_ieds(ied_file):
        has_all_aps = ied_dict['AP complets ? Oui '].lower().strip() == 'oui'
        if has_all_aps:
            aiot = ied_dict['\ufeffCode AIOT']
            print(f"--- IED {aiot}")

            try:
                ied_data = get_icpe(aiot)
            except requests.HTTPError as err:
                print(f'Failed to get ICPE {aiot} from georisques')
                print(err)

            ied_documents = ied_data.get('documentsHorsInspection', [])
            if not ied_documents:
                print(f'warning : no document found for ICPE {aiot}')

            ied_dir = out_dir / aiot
            if not ied_dir.is_dir():
                os.mkdir(ied_dir)

            for document_data in ied_documents:
                try:
                    type_fichier = {
                        "ap prescriptions complémentaires": "APC",
                        'arrêté préfectoral': 'AP',
                        'arrêté de mise en demeure': 'AMD',
                    }[document_data['typeFichier'].lower()]
                except KeyError:
                    type_fichier = f"{document_data['typeFichier']}_RENAME_MANUALLY"
                
                file_name = f"{document_data['dateFichier']}_{type_fichier}.pdf"
                file_path = ied_dir / file_name
                if file_path.is_file():
                    print(f"file {file_name} already exists, continue ...")
                    continue

                print(f"dowloading file {file_name} ...")
                with requests.get(document_data['urlFichier'], stream=True) as r:
                    r.raise_for_status()
                    with open(file_path, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192): 
                            f.write(chunk)



if __name__ == '__main__':
    import sys
    from optparse import OptionParser
    
    parser = OptionParser()
    parser.add_option("--limit", default=None, type="int")
    parser.add_option("-i", "--ied-file", default='./tmp/20240813_permis_consolidés_état_des_lieux_MAJ_27_aout_2024 annoté.csv')
    parser.add_option("-o", "--ap-dir", default='./tmp/APs-georisques')
    (options, args) = parser.parse_args()

    ied_file = Path(options.ied_file)
    ap_dir = Path(options.ap_dir)

    main(ied_file, ap_dir)
