from typing import List
from pathlib import Path

from optparse import OptionParser
from .settings import TEST_DATA_DIR
from .segmentation_arrete.parse_arrete import parse_arrete
from .detection_references.arretes_references import parse_arretes_references


def main(lines: List[str]):
    soup = parse_arrete(lines)
    for element in soup.select('*'):
        new_children = parse_arretes_references(soup, element.children)
        element.clear()
        element.extend(new_children)
    return soup


if __name__ == "__main__":
    PARSER = OptionParser()
    PARSER.add_option(
        "-i",
        "--input",
        default=TEST_DATA_DIR / "arretes_ocr" / "2020-04-20_AP-auto_initial_pixtral.txt",
    )
    PARSER.add_option(
        "-o",
        "--output",
        default='./tmp/output.html',
    )
    (options, args) = PARSER.parse_args()

    with open(Path(options.input), 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    soup = main(lines)
    with open(Path(options.output), 'w', encoding='utf-8') as f:
        f.write(soup.prettify())
