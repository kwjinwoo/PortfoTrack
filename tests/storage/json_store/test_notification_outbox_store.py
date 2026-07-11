"""Tests for local snapshot-summary outbox persistence."""

import json

from portfotrack.storage.json_store import notification_outbox_store


def test_save_writes_versioned_human_readable_json(tmp_path, monkeypatch) -> None:
    """Outbox artifacts use deterministic names and explicit UTF-8 JSON."""
    monkeypatch.setattr(notification_outbox_store, "NOTIFICATION_OUTBOX_DIR", tmp_path)
    summary = {
        "schema_version": "1.0",
        "kind": "snapshot_summary",
        "snapshot_date": "2026-07-11",
        "message": "요약 메시지",
    }

    path = notification_outbox_store.save(summary)

    assert path == tmp_path / "snapshot_summary_2026-07-11_v1.json"
    assert json.loads(path.read_text(encoding="utf-8")) == summary
    assert "\n  \"message\"" in path.read_text(encoding="utf-8")
