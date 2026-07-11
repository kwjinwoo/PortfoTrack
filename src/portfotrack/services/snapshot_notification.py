"""Orchestration for queueing and delivering saved snapshot notifications."""

import portfotrack.path as path_mod
from portfotrack.domain.snapshot import Snapshot
from portfotrack.integrations.telegram import (
    load_telegram_config,
    process_outbox,
)
from portfotrack.services.snapshot_summary import queue_snapshot_summary


def notify_snapshot_saved(snapshot: Snapshot) -> tuple[int, int]:
    """Queue a saved snapshot summary and attempt all pending deliveries.

    Missing credentials leave the new artifact pending. When a target is not
    configured and no new artifact is produced, existing pending artifacts are
    still eligible for retry.

    Args:
        snapshot: Snapshot that has already been persisted successfully.

    Returns:
        Pair of fully sent and failed pending artifact counts.
    """
    queued_path = queue_snapshot_summary(snapshot)
    config = load_telegram_config()
    if config is None:
        return (0, 0)
    outbox = queued_path.parent if queued_path is not None else path_mod.NOTIFICATION_OUTBOX_DIR
    return process_outbox(outbox, config)
