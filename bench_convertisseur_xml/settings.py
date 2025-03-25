import logging
import locale
import pathlib

from dotenv import load_dotenv

load_dotenv()
locale.setlocale(locale.LC_ALL, 'fr')

LOGGER = logging.getLogger('bench-convertisseur-xml')
LOGGER.setLevel(level=logging.INFO)
LOGGER.addHandler(logging.StreamHandler())

APP_ROOT = pathlib.Path(__file__).resolve().parent.parent

TEST_DATA_DIR = APP_ROOT / 'test_data'
TMP_DATA_DIR = APP_ROOT / 'tmp'

OCR_FILE_EXTENSION = '.md'
