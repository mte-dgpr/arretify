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

import json

# CSV list of French addresses : https://adresse.data.gouv.fr/data/ban/adresses/latest/csv
import re
from csv import DictReader
from pathlib import Path
from typing import Set

from arretify.law_data.french_addresses import WAY_TYPES

# Reject street names that are just way types or empty
REJECTED_STREET_NAMES = (
    {way_type for way_type in WAY_TYPES} | {way_type.title() for way_type in WAY_TYPES} | {""}
)


def main(input_path: Path, output_dir_path: Path):
    street_names: Set[str] = set()

    with open(input_path, "r", encoding="utf-8") as f:
        reader = DictReader(f, delimiter=";")
        for row in reader:
            if row["nom_voie"]:
                street_name = row["nom_voie"]
                street_name = re.sub(r"\s+", " ", street_name).strip()
                if row["nom_voie"] in REJECTED_STREET_NAMES:
                    continue
                street_names.add(street_name)

    street_names_path = output_dir_path / "french_street_names.json"
    with open(street_names_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(sorted(street_names), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    from optparse import OptionParser

    from dotenv import load_dotenv

    load_dotenv()

    parser = OptionParser()
    parser.add_option("-i", "--input", default="./tmp/adresses-france.csv")
    parser.add_option("-o", "--output", default="./tmp")
    (options, args) = parser.parse_args()

    input_path = Path(options.input)
    output_dir_path = Path(options.output)

    main(input_path, output_dir_path)

    print("DONE !!! Don't forget to clean the output files manually if needed.")
