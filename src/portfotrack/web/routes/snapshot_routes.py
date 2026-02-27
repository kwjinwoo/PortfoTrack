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
    save_snapshot_overwrite,
)
from portfotrack.services.target_services import (
    load_latest_target,
    validate_asset_id_in_target,
)
from portfotrack.storage.json_store.errors import SnapshotNotFoundError
from portfotrack.storage.json_store.snapshot_store import load as store_load
from portfotrack.storage.serialization.snapshot_json import (
    dto_to_snapshot,
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

    error_resp, status = _validate_items(items)
    if error_resp is not None:
        return error_resp, status

    error_resp, status = _validate_asset_ids_against_target(items)
    if error_resp is not None:
        return error_resp, status

    snapshot = init_snapshot()
    for item in items:
        add_item_to_snapshot(snapshot, item["asset_id"], item["label"], item["amount"])

    save_snapshot(snapshot)
    dto = snapshot_to_dto(snapshot)
    return jsonify(dto), 201


def _validate_items(items: list) -> tuple[None, None] | tuple[object, int]:
    """Validate a list of item dicts for required fields and types.

    Args:
        items: List of item dicts to validate.

    Returns:
        (None, None) if valid, or (error_response, status_code) if invalid.
    """
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

    return None, None


def _validate_asset_ids_against_target(
    items: list,
) -> tuple[None, None] | tuple[object, int]:
    """Validate item asset_ids against the latest target allocation.

    If no target exists, validation is skipped and items are accepted.

    Args:
        items: List of item dicts with 'asset_id' keys.

    Returns:
        (None, None) if valid or no target, or (error_response, status_code) if invalid.
    """
    try:
        target = load_latest_target()
    except FileNotFoundError:
        target = None

    if target is not None:
        for item in items:
            aid = item["asset_id"]
            if not validate_asset_id_in_target(target, aid):
                valid_ids = target.get_asset_ids()
                return (
                    jsonify(
                        {
                            "error": f"Invalid asset_id '{aid}'. "
                            f"Valid asset ids: {valid_ids}"
                        }
                    ),
                    400,
                )

    return None, None


@snapshot_bp.route("/<date>", methods=["PUT"])
def update_snapshot(date: str):
    """Update an existing snapshot with full replacement.

    Expects JSON body with ``mode`` and ``items`` fields.
    Mode determines save behavior:
    - ``"overwrite"``: replaces the original file, preserving its date.
    - ``"new"``: saves as a new snapshot with today's date.

    Args:
        date: ISO date string (YYYY-MM-DD) of the snapshot to update.

    Returns:
        200 with updated snapshot DTO for overwrite mode,
        201 with new snapshot DTO for new mode,
        or 400/404 on validation failure.
    """
    if not _DATE_PATTERN.match(date):
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400

    body = request.get_json(silent=True)
    if body is None:
        return jsonify({"error": "Request body must be valid JSON."}), 400

    mode = body.get("mode")
    if mode not in ("overwrite", "new"):
        return (
            jsonify({"error": "'mode' must be 'overwrite' or 'new'."}),
            400,
        )

    items = body.get("items")
    if not items or not isinstance(items, list) or len(items) == 0:
        return jsonify({"error": "'items' must be a non-empty list."}), 400

    error_resp, status = _validate_items(items)
    if error_resp is not None:
        return error_resp, status

    # Verify the source snapshot exists
    matching = list(path_mod.SNAPSHOTS_DIR.glob(f"snapshot_{date}_v*.json"))
    if not matching:
        return jsonify({"error": f"Snapshot for {date} not found."}), 404

    error_resp, status = _validate_asset_ids_against_target(items)
    if error_resp is not None:
        return error_resp, status

    # Build the updated snapshot
    snapshot = init_snapshot()
    for item in items:
        add_item_to_snapshot(snapshot, item["asset_id"], item["label"], item["amount"])

    if mode == "overwrite":
        snapshot.date = date
        latest_file = sorted(matching)[-1]
        save_snapshot_overwrite(snapshot, latest_file.name)
        dto = snapshot_to_dto(snapshot)
        return jsonify(dto), 200
    else:  # mode == "new"
        save_snapshot(snapshot)
        dto = snapshot_to_dto(snapshot)
        return jsonify(dto), 201


def _validate_item_fields(body: dict) -> tuple[str, str, int] | tuple[None, None, None]:
    """Extract and validate item fields from a request body.

    Returns:
        (asset_id, label, amount) if valid, or (None, None, None) if invalid.
    """
    asset_id = body.get("asset_id")
    label = body.get("label")
    amount = body.get("amount")

    if not asset_id or not isinstance(asset_id, str):
        return None, None, None
    if not label or not isinstance(label, str):
        return None, None, None
    if amount is None or not isinstance(amount, int) or isinstance(amount, bool):
        return None, None, None

    return asset_id, label, amount


@snapshot_bp.route("/<date>/items", methods=["POST"])
def add_item(date: str):
    """Add an item to an existing snapshot.

    Loads the snapshot for the given date, adds the new item (merging
    if asset_id+label match), saves back to disk, and returns the
    updated snapshot.

    Args:
        date: ISO date string (YYYY-MM-DD).

    Returns:
        200 with updated snapshot DTO, or 400/404 error.
    """
    if not _DATE_PATTERN.match(date):
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400

    body = request.get_json(silent=True)
    if body is None:
        return jsonify({"error": "Request body must be valid JSON."}), 400

    asset_id, label, amount = _validate_item_fields(body)
    if asset_id is None:
        return (
            jsonify(
                {
                    "error": "Item must have 'asset_id' (str), 'label' (str), and 'amount' (int)."
                }
            ),
            400,
        )

    # Load existing snapshot
    matching = list(path_mod.SNAPSHOTS_DIR.glob(f"snapshot_{date}_v*.json"))
    if not matching:
        return jsonify({"error": f"Snapshot for {date} not found."}), 404

    latest_file = sorted(matching)[-1]
    try:
        dto = store_load(latest_file.name)
    except SnapshotNotFoundError:
        return jsonify({"error": f"Snapshot for {date} not found."}), 404

    snapshot = dto_to_snapshot(dto)
    add_item_to_snapshot(snapshot, asset_id, label, amount)
    save_snapshot(snapshot)

    updated_dto = snapshot_to_dto(snapshot)
    return jsonify(updated_dto)
