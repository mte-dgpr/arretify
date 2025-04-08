from typing import List, Iterator, Tuple
from pathlib import Path
from optparse import OptionParser
import traceback

from bs4 import BeautifulSoup

from .settings import TEST_DATA_DIR, LOGGER, OCR_FILE_EXTENSION
from .arrete_segmentation.parse_arrete import parse_arrete
from .references_detection.sections_detection import parse_section_references
from .references_detection.arretes_detection import parse_arretes_references
from .references_detection.decrets_detection import parse_decrets_references
from .references_detection.circulaires_detection import parse_circulaires_references
from .references_detection.codes_detection import parse_codes_references
from .references_detection.self_detection import parse_self_references
from .references_detection.eu_acts_detection import parse_eu_acts_references
from .references_resolution.core import resolve_document_references, resolve_section_references
from .references_resolution.codes_resolution import resolve_code_article_legifrance_id, resolve_code_legifrance_id
from .references_resolution.sections_resolution import match_sections_with_documents
from .references_resolution.arretes_resolution import resolve_arrete_ministeriel_legifrance_id
from .references_resolution.decrets_resolution import resolve_decret_legifrance_id
from .references_resolution.circulaires_resolution import resolve_circulaire_legifrance_id
from .references_resolution.eu_acts_resolution import resolve_eu_decision_eurlex_url, resolve_eu_directive_eurlex_url, resolve_eu_regulation_eurlex_url
from .law_data.types import DocumentType
from .operations_detection.operations import parse_operations
from .clean_ocrized_file import clean_ocrized_file
from .html_schemas import ALINEA_SCHEMA, DOCUMENT_REFERENCE_SCHEMA, VISA_SCHEMA, MOTIF_SCHEMA
from .utils.html import make_css_class
from .debug import insert_debug_keywords
from .parsing_utils.source_mapping import initialize_lines, TextSegments
from .types import PageElementOrString

ALINEA_CSS_CLASS = make_css_class(ALINEA_SCHEMA)
DOCUMENT_REFERENCE_CSS_CLASS = make_css_class(DOCUMENT_REFERENCE_SCHEMA)

MOTIF_CSS_CLASS = make_css_class(MOTIF_SCHEMA)
VISA_CSS_CLASS = make_css_class(VISA_SCHEMA)


def ocrized_arrete_to_html(lines: TextSegments) -> BeautifulSoup:
    lines = clean_ocrized_file(lines)
    soup = parse_arrete(lines)
    new_children: List[PageElementOrString]

    # Detect all references
    for element in soup.select(f'.{ALINEA_CSS_CLASS}, .{ALINEA_CSS_CLASS} *, .{MOTIF_CSS_CLASS}, .{VISA_CSS_CLASS}'):
        new_children = list(element.children)
        new_children = parse_arretes_references(soup, new_children)
        new_children = parse_decrets_references(soup, new_children)
        new_children = parse_circulaires_references(soup, new_children)
        new_children = parse_codes_references(soup, new_children)
        new_children = parse_self_references(soup, new_children)
        new_children = parse_eu_acts_references(soup, new_children)
        new_children = parse_section_references(soup, new_children)
        element.clear()
        element.extend(new_children)

    # Resolve all document references
    resolve_document_references(soup, DocumentType.arrete_ministeriel, resolve_arrete_ministeriel_legifrance_id)
    resolve_document_references(soup, DocumentType.decret, resolve_decret_legifrance_id)
    resolve_document_references(soup, DocumentType.circulaire, resolve_circulaire_legifrance_id)
    resolve_document_references(soup, DocumentType.code, resolve_code_legifrance_id)
    resolve_document_references(soup, DocumentType.eu_decision, resolve_eu_decision_eurlex_url)
    resolve_document_references(soup, DocumentType.eu_regulation, resolve_eu_regulation_eurlex_url)
    resolve_document_references(soup, DocumentType.eu_directive, resolve_eu_directive_eurlex_url)

    # Match sections with documents,
    for element in soup.select(f'.{ALINEA_CSS_CLASS}, .{ALINEA_CSS_CLASS} *, .{MOTIF_CSS_CLASS}, .{VISA_CSS_CLASS}'):
        new_children = list(element.children)
        new_children = match_sections_with_documents(soup, new_children)
        element.clear()
        element.extend(new_children)

    # Resolve all section references
    resolve_section_references(soup, DocumentType.code, resolve_code_article_legifrance_id)

    # Find consolidation operations
    for container in soup.select(f'.{ALINEA_CSS_CLASS}, .{ALINEA_CSS_CLASS} *'):
        new_children = list(container.children)

        arretes_references = container.select(f'.{DOCUMENT_REFERENCE_CSS_CLASS}')
        if arretes_references:
            new_children = parse_operations(soup, new_children)

        container.clear()
        container.extend(new_children)
    return soup


def main(input_path: Path, output_path: Path):
    with open(input_path, 'r', encoding='utf-8') as f:
        raw_lines = f.readlines()
    lines = initialize_lines(raw_lines)
    soup = ocrized_arrete_to_html(lines)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(soup.prettify())


def _walk_ocrized_files(dir_path: Path) -> Iterator[Tuple[Path, Path]]:
    for root, _, file_names in input_path.walk():
        ocrized_file_paths = [
            root / file_name for file_name in file_names 
            if file_name.endswith(OCR_FILE_EXTENSION)
        ]
        for ocrized_file_path in ocrized_file_paths:
            yield root.relative_to(dir_path), ocrized_file_path


if __name__ == "__main__":
    PARSER = OptionParser()
    PARSER.add_option(
        "-i",
        "--input",
        help="Input folder or single file path.",
        default=TEST_DATA_DIR / "arretes_ocr",
    )
    PARSER.add_option(
        "-o",
        "--output",
        default=TEST_DATA_DIR / "arretes_html",
    )
    (options, args) = PARSER.parse_args()

    input_path = Path(options.input)
    output_path = Path(options.output)

    if input_path.is_dir():
        if not output_path.is_dir():
            LOGGER.error(f'Expected output to be a directory, got {output_path}')
        ocrized_files_walk = list(_walk_ocrized_files(input_path))
        for i, (relative_root, ocrized_file_path) in enumerate(ocrized_files_walk):
            output_root = output_path / relative_root
            # Makes sure output dir exists
            output_root.mkdir(parents=True, exist_ok=True)
            html_file_path = output_root / f'{ocrized_file_path.stem}.html'
            LOGGER.info(f'[{i + 1}/{len(ocrized_files_walk)}] parsing {ocrized_file_path} ...')
            try:
                main(ocrized_file_path, html_file_path)
            except BaseException as err:
                LOGGER.error(f'[{i + 1}/{len(ocrized_files_walk)}] FAILED : {ocrized_file_path} ...')
                print(traceback.format_exc())

    else:
        main(input_path, output_path)

