"""Snapshot API routes.

Provides endpoints for listing, retrieving, and creating portfolio snapshots.
All endpoints delegate to the services layer; no domain logic is performed here.
"""

import re

from flask import Blueprint, jsonify, request

import portfotrack.path as path_mod
from portfotrack.services.snapshot_services import (
    add_item_to_snapshot,
    init_snapshot,
    save_snapshot,
)
from portfotrack.storage.json_store.errors import SnapshotNotFoundError
from portfotrack.storage.json_store.snapshot_store import load as store_load
from portfotrack.storage.serialization.snapshot_json import (
    snapshot_to_dto,
)

_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")

snapshot_bp = Blueprint("snapshots", __name__, url_prefix="/api/snapshots")


@snapshot_bp.route("", methods=["GET"])
def list_snapshots():
    """List available snapshot dates.

    Returns:
        JSON array of objects with date and filename fields,
        sorted by date ascending.
    """
    files = sorted(path_mod.SNAPSHOTS_DIR.glob("snapshot_*.json"))
    result = []
    for f in files:
        # Extract date from filename pattern: snapshot_YYYY-MM-DD_v1.json
        parts = f.stem.split("_")
        if len(parts) >= 2:
            date = parts[1]
            result.append({"date": date, "filename": f.name})
    return jsonify(result)


@snapshot_bp.route("/<date>", methods=["GET"])
def get_snapshot(date: str):
    """Load a specific snapshot by date.

    Args:
        date: ISO date string (YYYY-MM-DD).

    Returns:
        JSON representation of the snapshot, or 400/404 error.
    """
    if not _DATE_PATTERN.match(date):
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400

    # Find matching file
    matching = list(path_mod.SNAPSHOTS_DIR.glob(f"snapshot_{date}_v*.json"))
    if not matching:
        return jsonify({"error": f"Snapshot for {date} not found."}), 404

    latest_file = sorted(matching)[-1]
    try:
        dto = store_load(latest_file.name)
    except SnapshotNotFoundError:
        return jsonify({"error": f"Snapshot for {date} not found."}), 404

    return jsonify(dto)


@snapshot_bp.route("", methods=["POST"])
def create_snapshot():
    """Create and persist a new snapshot.

    Expects JSON body with an ``items`` list. Each item must have
    ``asset_id``, ``label``, and ``amount`` fields.

    Returns:
        201 with the created snapshot DTO, or 400 on validation failure.
    """
    body = request.get_json(silent=True)
    if body is None:
        return jsonify({"error": "Request body must be valid JSON."}), 400

    items = body.get("items")
    if not items or not isinstance(items, list) or len(items) == 0:
        return jsonify({"error": "'items' must be a non-empty list."}), 400

    snapshot = init_snapshot()

    for item in items:
        if not isinstance(item, dict):
            return jsonify({"error": "Each item must be an object."}), 400

        asset_id = item.get("asset_id")
        label = item.get("label")
        amount = item.get("amount")

        if not asset_id or not isinstance(asset_id, str):
            return jsonify({"error": "Each item must have a string 'asset_id'."}), 400
        if not label or not isinstance(label, str):
            return jsonify({"error": "Each item must have a string 'label'."}), 400
        if amount is None or not isinstance(amount, int) or isinstance(amount, bool):
            return jsonify({"error": "Each item must have an integer 'amount'."}), 400

        add_item_to_snapshot(snapshot, asset_id, label, amount)

    save_snapshot(snapshot)
    dto = snapshot_to_dto(snapshot)
    return jsonify(dto), 201
