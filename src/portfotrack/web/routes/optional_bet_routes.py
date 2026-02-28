"""Optional bet API routes.

Provides endpoints for listing, retrieving, creating, and managing
optional bet snapshots. All endpoints delegate to the services layer;
no domain logic is performed here.
"""

import re

from flask import Blueprint, jsonify

import portfotrack.path as path_mod
from portfotrack.services.optional_bet_services import (
    load_latest_optional_bet,
)
from portfotrack.storage.json_store.errors import OptionalBetNotFoundError
from portfotrack.storage.serialization.optional_bet_json import optional_bet_to_dto

_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")

optional_bet_bp = Blueprint("optional_bets", __name__, url_prefix="/api/optional-bets")


@optional_bet_bp.route("", methods=["GET"])
def list_optional_bets():
    """List available optional bet files.

    Returns:
        JSON array of objects with date and filename fields,
        sorted by date ascending.
    """
    files = sorted(path_mod.OPTIONAL_BETS_DIR.glob("optional_bet_*.json"))
    result = []
    for f in files:
        parts = f.stem.split("_")
        if len(parts) >= 3:
            date = parts[2]
            result.append({"date": date, "filename": f.name})
    return jsonify(result)


@optional_bet_bp.route("/latest", methods=["GET"])
def get_latest():
    """Load the latest optional bet snapshot.

    Returns:
        JSON representation of the latest snapshot, or 404 if none exists.
    """
    try:
        snapshot = load_latest_optional_bet()
    except OptionalBetNotFoundError:
        return jsonify({"error": "No optional bet snapshot found."}), 404

    dto = optional_bet_to_dto(snapshot)
    return jsonify(dto)
