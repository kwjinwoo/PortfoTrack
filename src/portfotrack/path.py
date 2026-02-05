from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parent.parent


DATA_DIR = PROJECT_ROOT / "data"

TARGETS_DIR = DATA_DIR / "targets"
