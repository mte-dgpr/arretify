import logging
import pathlib

from dotenv import load_dotenv

load_dotenv()

LOGGER = logging.getLogger('bench-convertisseur-xml')
LOGGER.setLevel(level=logging.INFO)
LOGGER.addHandler(logging.StreamHandler())

APP_ROOT = pathlib.Path(__file__).resolve().parent.parent

TEST_DATA_DIR = APP_ROOT / 'test_data'