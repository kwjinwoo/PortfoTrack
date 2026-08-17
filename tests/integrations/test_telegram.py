"""Tests for the integrated Telegram notification transport."""

import json
from pathlib import Path

from portfotrack.integrations.telegram import (
    TelegramConfig,
    load_dotenv,
    load_telegram_config,
    process_outbox,
    send_message,
    split_message,
)


class FakeResponse:
    """Minimal context-managed HTTP response."""

    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


def test_load_dotenv_supports_comments_whitespace_and_quotes(tmp_path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "# Telegram settings\n"
        " TELEGRAM_BOT_TOKEN = 'secret-token' \n"
        'TELEGRAM_CHAT_ID="12345"\n',
        encoding="utf-8",
    )

    assert load_dotenv(env_file) == {
        "TELEGRAM_BOT_TOKEN": "secret-token",
        "TELEGRAM_CHAT_ID": "12345",
    }


def test_configuration_loads_dotenv_without_shell_exports(
    tmp_path, monkeypatch
) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "TELEGRAM_BOT_TOKEN=file-token\nTELEGRAM_CHAT_ID=file-chat\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)

    config = load_telegram_config(env_file)

    assert config == TelegramConfig(token="file-token", chat_id="file-chat")


def test_process_environment_overrides_dotenv(tmp_path, monkeypatch) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "TELEGRAM_BOT_TOKEN=file-token\nTELEGRAM_CHAT_ID=file-chat\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "process-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "process-chat")

    config = load_telegram_config(env_file)

    assert config == TelegramConfig(token="process-token", chat_id="process-chat")


def test_missing_credentials_disable_optional_delivery(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)

    assert load_telegram_config(tmp_path / ".env") is None


def test_split_message_preserves_text_within_telegram_limit() -> None:
    text = "\n".join(["자산군 " + ("가" * 900) for _ in range(6)])

    chunks = split_message(text)

    assert len(chunks) > 1
    assert all(1 <= len(chunk) <= 4096 for chunk in chunks)
    assert "\n".join(chunks) == text


def test_send_message_posts_json_without_parse_mode() -> None:
    requests = []

    def opener(request, timeout):
        requests.append((request, timeout))
        return FakeResponse({"ok": True})

    send_message("secret-token", "12345", "요약", opener=opener)

    request, timeout = requests[0]
    payload = json.loads(request.data.decode("utf-8"))
    assert request.full_url.endswith("/botsecret-token/sendMessage")
    assert payload == {"chat_id": "12345", "text": "요약"}
    assert timeout == 15


def test_process_outbox_moves_file_only_after_all_chunks_send(tmp_path) -> None:
    artifact = _write_artifact(tmp_path)
    sent_messages = []

    result = process_outbox(
        tmp_path,
        TelegramConfig(token="token", chat_id="chat"),
        sender=lambda token, chat_id, text: sent_messages.append(text),
    )

    assert result == (1, 0)
    assert sent_messages == ["요약 메시지"]
    assert not artifact.exists()
    assert (tmp_path / "sent" / artifact.name).exists()


def test_process_outbox_leaves_failed_artifact_for_retry(tmp_path) -> None:
    artifact = _write_artifact(tmp_path)

    def fail_sender(token, chat_id, text):
        raise RuntimeError("temporary failure")

    result = process_outbox(
        tmp_path,
        TelegramConfig(token="token", chat_id="chat"),
        sender=fail_sender,
    )

    assert result == (0, 1)
    assert artifact.exists()
    assert not (tmp_path / "sent" / artifact.name).exists()


def _write_artifact(outbox: Path) -> Path:
    artifact = outbox / "snapshot_summary_2026-07-11_v1.json"
    artifact.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "kind": "snapshot_summary",
                "snapshot_date": "2026-07-11",
                "message": "요약 메시지",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return artifact
