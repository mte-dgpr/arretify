from pathlib import Path
from typing import Dict, List
from datetime import datetime
import json

from arretify.types import SessionContext
from arretify.utils.scripts import load_settings_from_env
from arretify.law_data.apis.legifrance import initialize_legifrance_client
from arretify._vendor.clients_api_droit.clients_api_droit.legifrance import (  # noqa: E402
    list_codes,
    get_code_summary,
    iter_articles,
)


def download_codes(session_context: SessionContext, output_dir: Path):
    print("Downloading code data...")
    assert session_context.legifrance_client is not None, "Legifrance client is not initialized"
    code_data = dict(
        version=datetime.now().isoformat(),
        data=list(list_codes(session_context.legifrance_client)),
    )
    code_data_path = output_dir / "codes.json"
    print(f"Saving code data in {code_data_path}")
    with open(code_data_path, "w", encoding="utf-8") as f:
        json.dump(code_data, f, indent=2, ensure_ascii=False)


def download_code_index(session_context: SessionContext, output_dir: Path, code_id: str):
    assert session_context.legifrance_client is not None, "Legifrance client is not initialized"
    code_root_section = get_code_summary(session_context.legifrance_client, code_id)
    articles: List[Dict] = []

    for _, (__, article) in enumerate(iter_articles([code_root_section])):
        articles.append(
            dict(
                num=article["num"],
                id=article["id"],
                cid=article["cid"],
            )
        )

    print(f"Found {len(articles)} articles for code {code_id}...")
    articles_data = dict(version=datetime.now().isoformat(), data=articles)
    articles_data_path = output_dir / f"code_index_{code_id}.json"
    print(f"Saving articles data in {articles_data_path}")
    with open(articles_data_path, "w", encoding="utf-8") as f:
        json.dump(articles_data, f, indent=2, ensure_ascii=False)


def main(session_context: SessionContext, output_dir: Path):
    download_codes(session_context, output_dir)
    # code de l'environnement
    download_code_index(session_context, output_dir, "LEGITEXT000006074220")
    # code du travail
    download_code_index(session_context, output_dir, "LEGITEXT000006072050")


if __name__ == "__main__":
    from optparse import OptionParser
    from dotenv import load_dotenv

    load_dotenv()
    session_context = SessionContext(
        settings=load_settings_from_env(),
    )
    session_context = initialize_legifrance_client(session_context)

    parser = OptionParser()
    parser.add_option("-o", "--output-dir", default="./tmp")
    (options, args) = parser.parse_args()

    output_dir = Path(options.output_dir)
    main(session_context, output_dir)
