import os
from pathlib import Path

from bench_convertisseur_xml.settings import TEST_DATA_DIR
from bench_convertisseur_xml.settings import LOGGER
from .main import ocrized_arrete_to_html

ARRETES_OCR_DIR = TEST_DATA_DIR / 'arretes_ocr'
ARRETES_HTML_DIR = TEST_DATA_DIR / 'arretes_html'

ARRETES_FILE_NAMES = [
    '1978-05-24_AP-auto_pixtral.txt',
    '2002-03-04_AP-auto_refonte_pixtral.txt',
    '2004-05-04_APC-auto_pixtral.txt',
    '2008-12-10_AP_pixtral.txt',
    '2009-12-18_AP_pixtral.txt',
    '2010-12-24_AP_pixtral.txt',
    '2011-02-24_AP-auto_pixtral.txt',
    '2012-04-03_AP_pixtral.txt',
    '2012-12-07_AP_pixtral.txt',
    '2017-01-26_APC-garanties-financières_pixtral.txt',
    '2020-04-20_AP_pixtral.txt',
    '2020-12-22_AP_pixtral.txt',
    '2021-09-24_AP_pixtral.txt',
    '2023-02-22_APC_pixtral.txt',
]


def _iter_parsed_arretes_ocr_files():
    arretes_ocr_file_paths = Path(ARRETES_OCR_DIR).rglob("*.txt")
    for arrete_ocr_file_path in arretes_ocr_file_paths:
        arrete_contents = open(arrete_ocr_file_path, 'r', encoding='utf-8').readlines()
        soup = ocrized_arrete_to_html(arrete_contents)
        yield arrete_ocr_file_path, soup.prettify()


def write_parse_arrete_snapshots():
    LOGGER.info('Generating snapshots ...')
    for arrete_ocr_file_path, arrete_html_str in _iter_parsed_arretes_ocr_files():
        LOGGER.info(f'Input {arrete_ocr_file_path.parent.name}/{arrete_ocr_file_path.stem} ...')
        arrete_html_file_path = ARRETES_HTML_DIR / f'{arrete_ocr_file_path.parent.name}/{arrete_ocr_file_path.stem}.html'
        arrete_html_file_path.parent.mkdir(parents=True, exist_ok=True)  # create subdirectories
        open(arrete_html_file_path, 'w', encoding='utf-8').write(arrete_html_str)


def test_parse_arrete_snapshots():
    LOGGER.info('Testing snapshots')
    for arrete_ocr_file_path, actual_contents in _iter_parsed_arretes_ocr_files():
        LOGGER.info(f'Input {arrete_ocr_file_path.parent.name}/{arrete_ocr_file_path.stem} ...')
        arrete_html_file_path = ARRETES_HTML_DIR / f'{arrete_ocr_file_path.parent.name}/{arrete_ocr_file_path.stem}.html'
        expected_contents = open(arrete_html_file_path, 'r', encoding='utf-8').read()        
        assert actual_contents == expected_contents


if __name__ == '__main__':
    write_parse_arrete_snapshots()  # to overwrite snapshots
    # test_parse_arrete_snapshots()  # to check change in code does not break snapshots
