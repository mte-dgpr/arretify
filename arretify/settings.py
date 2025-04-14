import logging
import pathlib
import os
from datetime import datetime
from dotenv import load_dotenv


load_dotenv()
ENV = os.environ.get("ENV")

OCR_FILE_EXTENSION = ".md"

APP_ROOT = pathlib.Path(__file__).resolve().parent.parent
TEST_DATA_DIR = APP_ROOT / "test_data"
TMP_DATA_DIR = APP_ROOT / "tmp"

# Logger setup
LOGGER = logging.getLogger("arretify")
LOGGER.setLevel(level=logging.INFO)

# Console handler
CONSOLE_HANDLER = logging.StreamHandler()

# Log file
LOG_DIR = APP_ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE_PATH = LOG_DIR / f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"

FILE_HANDLER = logging.FileHandler(LOG_FILE_PATH, encoding="utf-8")

# Add handlers
if not LOGGER.hasHandlers():
    LOGGER.addHandler(CONSOLE_HANDLER)
    LOGGER.addHandler(FILE_HANDLER)
