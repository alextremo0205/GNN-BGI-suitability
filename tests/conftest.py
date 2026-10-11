import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Make lib/ and every pipeline stage in scripts/ importable from the tests.
sys.path.insert(0, str(PROJECT_ROOT))
for stage_folder in sorted((PROJECT_ROOT / "scripts").iterdir()):
    if stage_folder.is_dir():
        sys.path.insert(0, str(stage_folder))
