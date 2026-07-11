"""Optional Telegram delivery for local snapshot summary artifacts."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import portfotrack.path as path_mod

TELEGRAM_MESSAGE_LIMIT = 4096
DEFAULT_ENV_FILE = path_mod.PROJECT_ROOT / ".env"

Sender = Callable[[str, str, str], None]


@dataclass(frozen=True)
class TelegramConfig:
    """Credentials for one user-configured Telegram destination."""

    token: str
    chat_id: str


def load_dotenv(file_path: Path) -> dict[str, str]:
    """Read simple ``KEY=VALUE`` settings without mutating the environment.

    Args:
        file_path: Local settings file. A missing file means no file settings.

    Returns:
        Parsed key-value pairs with matching single or double quotes removed.

    Raises:
        RuntimeError: If a non-comment line is not a valid assignment.
    """
    if not file_path.exists():
        return {}

    values: dict[str, str] = {}
    for line_number, raw_line in enumerate(
        file_path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise RuntimeError(f"Invalid .env entry on line {line_number}.")
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            raise RuntimeError(f"Invalid .env key on line {line_number}.")
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        values[key] = value
    return values


def load_telegram_config(env_file: Path = DEFAULT_ENV_FILE) -> TelegramConfig | None:
    """Load optional Telegram credentials from process environment or `.env`.

    Process environment values take precedence over file values. Missing
    credentials disable notification delivery instead of breaking local
    portfolio workflows.

    Args:
        env_file: Git-ignored local settings file to read.

    Returns:
        Complete Telegram configuration, or ``None`` when either key is absent.
    """
    file_values = load_dotenv(env_file)
    token = os.environ.get(
        "TELEGRAM_BOT_TOKEN", file_values.get("TELEGRAM_BOT_TOKEN", "")
    )
    chat_id = os.environ.get(
        "TELEGRAM_CHAT_ID", file_values.get("TELEGRAM_CHAT_ID", "")
    )
    if not token or not chat_id:
        return None
    return TelegramConfig(token=token, chat_id=chat_id)


def split_message(text: str, limit: int = TELEGRAM_MESSAGE_LIMIT) -> list[str]:
    """Split plain text at line boundaries within Telegram's size limit.

    Args:
        text: Non-empty summary message.
        limit: Maximum characters in one message.

    Returns:
        Ordered chunks whose individual lengths do not exceed ``limit``.

    Raises:
        ValueError: If the text is empty or the limit is not positive.
    """
    if not text:
        raise ValueError("Notification message must not be empty.")
    if limit < 1:
        raise ValueError("Message limit must be positive.")

    chunks: list[str] = []
    current = ""
    for line in text.split("\n"):
        candidate = line if not current else f"{current}\n{line}"
        if len(candidate) <= limit:
            current = candidate
            continue
        if current:
            chunks.append(current)
            current = ""
        while len(line) > limit:
            chunks.append(line[:limit])
            line = line[limit:]
        current = line
    if current:
        chunks.append(current)
    return chunks


def send_message(
    token: str,
    chat_id: str,
    text: str,
    *,
    opener: Callable[..., Any] = urllib.request.urlopen,
) -> None:
    """Send one plain-text message through Telegram's HTTPS Bot API.

    Args:
        token: Secret bot token used only to construct the Telegram endpoint.
        chat_id: Destination chat identifier.
        text: One message chunk within Telegram's size limit.
        opener: Injectable HTTPS opener for deterministic tests.

    Raises:
        RuntimeError: If transport fails or Telegram rejects the message.
    """
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = json.dumps({"chat_id": chat_id, "text": text}).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with opener(request, timeout=15) as response:
            result = json.loads(response.read().decode("utf-8"))
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as error:
        raise RuntimeError("Telegram request failed.") from error
    if not isinstance(result, dict) or result.get("ok") is not True:
        raise RuntimeError("Telegram rejected the message.")


def process_outbox(
    outbox: Path,
    config: TelegramConfig,
    *,
    sender: Sender = send_message,
) -> tuple[int, int]:
    """Deliver pending summaries and archive only complete deliveries.

    Args:
        outbox: Directory containing versioned snapshot summary artifacts.
        config: Telegram credentials and destination.
        sender: Injectable single-message sender.

    Returns:
        Pair of fully sent and failed artifact counts. Failed files stay pending.
    """
    if not outbox.exists():
        return (0, 0)

    sent_count = 0
    failed_count = 0
    for artifact_path in sorted(outbox.glob("snapshot_summary_*_v*.json")):
        try:
            message = _load_message(artifact_path)
            for chunk in split_message(message):
                sender(config.token, config.chat_id, chunk)
            sent_dir = outbox / "sent"
            sent_dir.mkdir(parents=True, exist_ok=True)
            artifact_path.replace(sent_dir / artifact_path.name)
            sent_count += 1
        except (OSError, RuntimeError, TypeError, ValueError, json.JSONDecodeError):
            failed_count += 1
    return (sent_count, failed_count)


def _load_message(artifact_path: Path) -> str:
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    if not isinstance(artifact, dict):
        raise TypeError("Outbox artifact root must be an object.")
    if artifact.get("schema_version") != "1.0":
        raise ValueError("Unsupported snapshot summary schema version.")
    if artifact.get("kind") != "snapshot_summary":
        raise ValueError("Unsupported notification kind.")
    message = artifact.get("message")
    if not isinstance(message, str) or not message:
        raise TypeError("Outbox artifact message must be a non-empty string.")
    return message
