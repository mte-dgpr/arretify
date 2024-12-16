from pathlib import Path

from bench_convertisseur_xml.settings import TEST_DATA_DIR
from bench_convertisseur_xml.settings import LOGGER
from .main import parse_arrete

ARRETES_OCR_DIR = TEST_DATA_DIR / 'arretes_ocr'
ARRETES_HTML_DIR = TEST_DATA_DIR / 'arretes_html'

ARRETES_FILE_NAMES = [
    '1978-05-24_AP-auto_pixtral.txt',
    # '2002-03-04_AP-auto_refonte_pixtral.txt',
    '2004-05-04_APC-auto_pixtral.txt',
    '2011-02-24_AP-auto_pixtral.txt',
    '2017-01-26_APC-garanties-financières_pixtral.txt',
    '2020-04-20_AP-auto_initial_pixtral.txt',
    '2021-09-24_AP-auto_refonte_pixtral.txt',
    '2023-02-23_APC-auto_pixtral.txt',
]


def iter_parsed_arretes_ocr_files():
    for arrete_file_name in ARRETES_FILE_NAMES:
        arrete_contents = open(ARRETES_OCR_DIR / arrete_file_name, 'r', encoding='utf-8').readlines()
        soup = parse_arrete(arrete_contents)
        yield Path(arrete_file_name), soup.prettify()


def test_parse_arrete_snapshots():
    for arrete_file_name, actual_contents in iter_parsed_arretes_ocr_files():
        expected_contents = open(ARRETES_HTML_DIR / f'{arrete_file_name.stem}.html', 'r', encoding='utf-8').read()
        assert actual_contents == expected_contents


if __name__ == '__main__':
    LOGGER.info(f'Generating snapshots ...')
    for arrete_file_name, arrete_html_str in iter_parsed_arretes_ocr_files():
        LOGGER.info(f'Input {arrete_file_name.stem} ...')
        open(ARRETES_HTML_DIR / f'{arrete_file_name.stem}.html', 'w', encoding='utf-8').write(arrete_html_str)