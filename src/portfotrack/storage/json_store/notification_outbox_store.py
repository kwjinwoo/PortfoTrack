"""Local JSON outbox for external snapshot notification consumers."""

import json
from pathlib import Path

from portfotrack.path import NOTIFICATION_OUTBOX_DIR
from portfotrack.storage.serialization.notification_summary_json import (
    SnapshotSummaryDTO,
)

CURRENT_NOTIFICATION_SCHEMA_VERSION = 1


def save(summary: SnapshotSummaryDTO) -> Path:
    """Persist one deterministic snapshot summary for an external consumer.

    A repeated explicit save for the same snapshot date replaces the pending
    artifact so the bridge sends the latest locally generated facts.

    Args:
        summary: Fully formatted, consumer-neutral snapshot summary.

    Returns:
        Path to the written outbox artifact.
    """
    NOTIFICATION_OUTBOX_DIR.mkdir(parents=True, exist_ok=True)
    file_name = (
        f"snapshot_summary_{summary['snapshot_date']}_"
        f"v{CURRENT_NOTIFICATION_SCHEMA_VERSION}.json"
    )
    file_path = NOTIFICATION_OUTBOX_DIR / file_name
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(summary, file, ensure_ascii=False, indent=2)
    return file_path
