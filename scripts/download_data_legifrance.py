from pathlib import Path
from datetime import datetime
import json

from dotenv import load_dotenv
load_dotenv()
from clients_api_droit.legifrance import authenticate, list_codes


def main(output_dir: Path):
    tokens = authenticate()
    print("Downloading code data...")
    code_data = dict(
        version=datetime.now().isoformat(),
        data=list(list_codes(tokens))
    )
    code_data_path = output_dir / 'codes.json'
    print(f"Saving code data in {code_data_path}")
    with open(code_data_path, 'w', encoding='utf-8') as f:
        json.dump(code_data, f, indent=2, ensure_ascii=False)
        

if __name__ == '__main__':
    import sys
    from optparse import OptionParser
    
    parser = OptionParser()
    parser.add_option("-o", "--output-dir", default='./tmp')
    (options, args) = parser.parse_args()

    output_dir = Path(options.output_dir)
    main(output_dir)
