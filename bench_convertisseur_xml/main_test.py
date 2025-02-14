# Pour re-générer les snapshots HTML, voir README, section "Snapshot testing".
import os
from pathlib import Path

from bench_convertisseur_xml.settings import TEST_DATA_DIR, LOGGER
from bench_convertisseur_xml.parsing_utils.source_mapping import initialize_lines

from .main import ocrized_arrete_to_html

ARRETES_OCR_DIR = TEST_DATA_DIR / 'arretes_ocr'
ARRETES_HTML_DIR = TEST_DATA_DIR / 'arretes_html'


def _iter_parsed_arretes_ocr_files():
    arretes_ocr_file_paths = Path(ARRETES_OCR_DIR).rglob("*.txt")
    for arrete_ocr_file_path in arretes_ocr_file_paths:
        arrete_contents = open(arrete_ocr_file_path, 'r', encoding='utf-8').readlines()
        soup = ocrized_arrete_to_html(initialize_lines(arrete_contents))
        yield arrete_ocr_file_path, soup.prettify()


def test_parse_arrete_snapshots():
    LOGGER.info('Testing snapshots')
    for arrete_ocr_file_path, actual_contents in _iter_parsed_arretes_ocr_files():
        LOGGER.info(f'Input {arrete_ocr_file_path.parent.name}/{arrete_ocr_file_path.stem} ...')
        arrete_html_file_path = ARRETES_HTML_DIR / f'{arrete_ocr_file_path.parent.name}/{arrete_ocr_file_path.stem}.html'
        expected_contents = open(arrete_html_file_path, 'r', encoding='utf-8').read()        
        assert actual_contents == expected_contents