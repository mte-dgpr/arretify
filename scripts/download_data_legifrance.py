from pathlib import Path
from typing import Dict, List
from datetime import datetime
import json

from dotenv import load_dotenv
load_dotenv()
from clients_api_droit.legifrance import authenticate, list_codes, get_code_summary, get_article, iter_articles


def download_codes(output_dir: Path):
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


def download_code_index(output_dir: Path, code_id: str):
    tokens = authenticate()
    code_root_section = get_code_summary(tokens, code_id)
    articles: List[Dict] = []

    for i, (parent_sections, article) in enumerate(iter_articles([code_root_section])):
        articles.append(dict(
            num=article['num'],
            id=article['id'],
            cid=article['cid'],
        ))

    print(f"Found {len(articles)} articles for code {code_id}...")
    articles_data = dict(
        version=datetime.now().isoformat(),
        data=articles
    )
    articles_data_path = output_dir / f'code_index_{code_id}.json'
    print(f"Saving articles data in {articles_data_path}")
    with open(articles_data_path, 'w', encoding='utf-8') as f:
        json.dump(articles_data, f, indent=2, ensure_ascii=False)


def main(output_dir: Path):
    download_codes(output_dir)
    download_code_index(output_dir, 'LEGITEXT000006074220')


if __name__ == '__main__':
    import sys
    from optparse import OptionParser
    
    parser = OptionParser()
    parser.add_option("-o", "--output-dir", default='./tmp')
    (options, args) = parser.parse_args()

    output_dir = Path(options.output_dir)
    main(output_dir)
