"""Project paths, read from the .env file at the root of the repository (see .env_example)."""

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

NETWORK = "Loenen - v8"

DATA_FOLDER_PATH = Path(os.getenv("DATA_FOLDER_PATH", PROJECT_ROOT / "data"))
NETWORK_FOLDER_PATH = DATA_FOLDER_PATH / NETWORK
METAMODEL_FILES_PATH = NETWORK_FOLDER_PATH / "metamodel_files"

SAVED_OBJECTS_FOLDER_PATH = Path(
    os.getenv("SAVED_OBJECTS_FOLDER_PATH", PROJECT_ROOT / "saved_objects")
)
RESULTS_FOLDER_PATH = Path(os.getenv("RESULTS_FOLDER_PATH", PROJECT_ROOT / "results"))
