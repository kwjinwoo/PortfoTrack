"""JSON shape for portable snapshot summary notifications."""

from typing import TypedDict


class SnapshotSummaryDTO(TypedDict):
    """Consumer-neutral message artifact for an external notification bridge."""

    schema_version: str
    kind: str
    snapshot_date: str
    message: str
