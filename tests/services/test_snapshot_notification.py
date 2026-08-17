"""Tests for integrated snapshot notification orchestration."""

from pathlib import Path

from portfotrack.domain.snapshot import Snapshot
from portfotrack.integrations.telegram import TelegramConfig
from portfotrack.services import snapshot_notification


def test_saved_snapshot_is_queued_then_pending_artifacts_are_delivered(
    tmp_path, monkeypatch
) -> None:
    snapshot = Snapshot(date="2026-07-11")
    queued_path = tmp_path / "snapshot_summary_2026-07-11_v1.json"
    calls = []
    monkeypatch.setattr(
        snapshot_notification,
        "queue_snapshot_summary",
        lambda value: calls.append(("queue", value)) or queued_path,
    )
    monkeypatch.setattr(
        snapshot_notification,
        "load_telegram_config",
        lambda: TelegramConfig(token="token", chat_id="chat"),
    )
    monkeypatch.setattr(
        snapshot_notification,
        "process_outbox",
        lambda outbox, config: calls.append(("deliver", outbox, config)) or (1, 0),
    )

    result = snapshot_notification.notify_snapshot_saved(snapshot)

    assert result == (1, 0)
    assert calls == [
        ("queue", snapshot),
        (
            "deliver",
            queued_path.parent,
            TelegramConfig(token="token", chat_id="chat"),
        ),
    ]


def test_missing_credentials_leave_summary_pending(tmp_path, monkeypatch) -> None:
    snapshot = Snapshot(date="2026-07-11")
    queued_path = tmp_path / "snapshot_summary_2026-07-11_v1.json"
    monkeypatch.setattr(
        snapshot_notification,
        "queue_snapshot_summary",
        lambda value: queued_path,
    )
    monkeypatch.setattr(
        snapshot_notification,
        "load_telegram_config",
        lambda: None,
    )

    assert snapshot_notification.notify_snapshot_saved(snapshot) == (0, 0)


def test_existing_pending_artifacts_retry_even_when_new_summary_is_not_queued(
    monkeypatch,
) -> None:
    snapshot = Snapshot(date="2026-07-11")
    config = TelegramConfig(token="token", chat_id="chat")
    monkeypatch.setattr(
        snapshot_notification,
        "queue_snapshot_summary",
        lambda value: None,
    )
    monkeypatch.setattr(snapshot_notification, "load_telegram_config", lambda: config)
    monkeypatch.setattr(
        snapshot_notification.path_mod, "NOTIFICATION_OUTBOX_DIR", Path("/outbox")
    )
    monkeypatch.setattr(
        snapshot_notification,
        "process_outbox",
        lambda outbox, loaded_config: (2, 0),
    )

    assert snapshot_notification.notify_snapshot_saved(snapshot) == (2, 0)
