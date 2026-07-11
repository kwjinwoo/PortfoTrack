from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parent.parent


DATA_DIR = PROJECT_ROOT / "data"

TARGETS_DIR = DATA_DIR / "targets"
SNAPSHOTS_DIR = DATA_DIR / "snapshots"
OPTIONAL_BETS_DIR = DATA_DIR / "optional_bets"
NOTIFICATION_OUTBOX_DIR = DATA_DIR / "notification_outbox"
