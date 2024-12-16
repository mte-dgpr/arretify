from pathlib import Path

from bs4 import BeautifulSoup

from .sentence_rules import is_not_information
from .utils import clean_markdown
from .header import parse_header
from .main_content import parse_main_content
from .parse_section import (
    identify_unique_sections, filter_max_level_sections
)
from bench_convertisseur_xml.html_schemas import HEADER_SCHEMA, MAIN_SCHEMA
from bench_convertisseur_xml.utils.html import make_element

TEMPLATE_PATH = Path(__file__).parent / 'template.html'
TEMPLATE_HTML = open(TEMPLATE_PATH, 'r', encoding='utf-8').read()

def main(input_file_path: Path, output_file_path: Path):
    with open(input_file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    lines = [
        clean_markdown(line) for line in lines 
        if not is_not_information(line)
    ]

    # Define sections that will be parsed and detected in this document
    unique_sections = identify_unique_sections(lines)
    authorized_sections = filter_max_level_sections(unique_sections)

    soup = BeautifulSoup(TEMPLATE_HTML, features="html.parser")
    body = soup.body
    assert body

    header = make_element(soup, HEADER_SCHEMA)
    body.append(header)
    lines = parse_header(soup, header, lines, authorized_sections)

    main_content = make_element(soup, MAIN_SCHEMA)
    body.append(main_content)
    parse_main_content(soup, main_content, lines, authorized_sections)

    with open(output_file_path, 'w', encoding='utf-8') as f:
        f.write(soup.prettify())


if __name__ == "__main__":
    from optparse import OptionParser
    from ..settings import TEST_DATA_DIR

    PARSER = OptionParser()
    PARSER.add_option(
        "-i",
        "--input",
        # default=TEST_DATA_DIR / "arretes_ocr" / "2020-04-20_AP-auto_initial_pixtral.txt",
        # default=TEST_DATA_DIR / "arretes_ocr" / "2021-09-24_AP-auto_refonte_pixtral.txt",
        # default=TEST_DATA_DIR / "arretes_ocr" / "2023-02-23_APC-auto_pixtral.txt",
        # default=TEST_DATA_DIR / "arretes_ocr" / "2011-02-24_AP-auto_pixtral.txt",
        # default=TEST_DATA_DIR / "arretes_ocr" / "2002-03-04_AP-auto_refonte_pixtral.txt",
        # default=TEST_DATA_DIR / "arretes_ocr" / "1978-05-24_AP-auto_pixtral.txt",
        default=TEST_DATA_DIR / "arretes_ocr" / "2017-01-26_APC-garanties-financières_pixtral.txt",
    )
    PARSER.add_option(
        "-o",
        "--output",
        default='./tmp/output.html',
    )
    (options, args) = PARSER.parse_args()

    main(Path(options.input), Path(options.output))
