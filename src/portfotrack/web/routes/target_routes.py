"""Target allocation API routes.

Provides endpoints for loading, creating, and managing target allocations.
All endpoints delegate to the services layer.
"""

import re

from flask import Blueprint, jsonify, request

import portfotrack.path as path_mod
from portfotrack.domain.target_allocation.errors import (
    DuplicateAssetError,
    InvalidTargetRatioError,
    InvalidToleranceBoundsError,
)
from portfotrack.services.target_services import (
    add_asset_to_target,
    get_available_assets_from_target,
    init_target,
    load_latest_target,
    save_target,
    save_target_overwrite,
)
from portfotrack.storage.serialization.target_json import target_to_dto

target_bp = Blueprint("targets", __name__, url_prefix="/api/targets")

_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@target_bp.route("", methods=["GET"])
def get_target():
    """Load the latest target allocation.

    Returns:
        JSON representation of the target allocation with a ``date`` field
        extracted from the source filename, or 404 if none exists.
    """
    try:
        target = load_latest_target()
    except FileNotFoundError:
        return jsonify({"error": "No target allocation found."}), 404

    # Extract date from the latest target filename
    target_files = sorted(path_mod.TARGETS_DIR.glob("*.json"))
    latest_name = target_files[-1].name if target_files else ""
    date_match = re.search(r"target_(\d{4}-\d{2}-\d{2})_v", latest_name)
    target_date = date_match.group(1) if date_match else ""

    dto = target_to_dto(target)
    return jsonify({**dto, "date": target_date})


@target_bp.route("", methods=["POST"])
def create_target():
    """Create a new empty target allocation and persist it.

    Returns:
        201 with the empty target DTO.
    """
    target = init_target()
    save_target(target)
    dto = target_to_dto(target)
    return jsonify(dto), 201


@target_bp.route("/assets", methods=["POST"])
def add_asset():
    """Add an asset to the current (latest) target allocation.

    Expects JSON body with: asset_id, asset_name, purpose,
    target_ratio, lower, upper.

    Returns:
        200 with updated target DTO, or 400/404/409 error.
    """
    body = request.get_json(silent=True)
    if body is None:
        return jsonify({"error": "Request body must be valid JSON."}), 400

    # Validate required fields
    required = ["asset_id", "asset_name", "purpose", "target_ratio", "lower", "upper"]
    for field in required:
        if field not in body:
            return jsonify({"error": f"Missing required field: '{field}'."}), 400

    asset_id = body["asset_id"]
    asset_name = body["asset_name"]
    purpose = body["purpose"]
    target_ratio = body["target_ratio"]
    lower = body["lower"]
    upper = body["upper"]

    # Type validation
    if not isinstance(asset_id, str) or not asset_id:
        return jsonify({"error": "'asset_id' must be a non-empty string."}), 400
    if not isinstance(asset_name, str) or not asset_name:
        return jsonify({"error": "'asset_name' must be a non-empty string."}), 400
    if not isinstance(purpose, str) or not purpose:
        return jsonify({"error": "'purpose' must be a non-empty string."}), 400
    if not isinstance(target_ratio, (int, float)) or isinstance(target_ratio, bool):
        return jsonify({"error": "'target_ratio' must be a number."}), 400
    if not isinstance(lower, (int, float)) or isinstance(lower, bool):
        return jsonify({"error": "'lower' must be a number."}), 400
    if not isinstance(upper, (int, float)) or isinstance(upper, bool):
        return jsonify({"error": "'upper' must be a number."}), 400

    # Load latest target
    try:
        target = load_latest_target()
    except FileNotFoundError:
        return jsonify({"error": "No target allocation found. Create one first."}), 404

    # Delegate to service (domain validates business rules)
    try:
        add_asset_to_target(
            target,
            asset_id,
            asset_name,
            purpose,
            float(target_ratio),
            float(lower),
            float(upper),
        )
    except DuplicateAssetError:
        return jsonify({"error": f"Asset '{asset_id}' already exists."}), 409
    except InvalidTargetRatioError:
        return jsonify({"error": "target_ratio must be between 0.0 and 1.0."}), 400
    except InvalidToleranceBoundsError as e:
        return jsonify({"error": f"Invalid tolerance bounds: {e}"}), 400

    save_target(target)
    dto = target_to_dto(target)
    return jsonify(dto)


@target_bp.route("/assets", methods=["GET"])
def list_target_assets():
    """List asset ids from the latest target allocation.

    Returns:
        JSON array of asset objects with id, name, and purpose fields,
        or 404 if no target allocation exists.
    """
    try:
        target = load_latest_target()
    except FileNotFoundError:
        return jsonify({"error": "No target allocation found."}), 404

    assets = get_available_assets_from_target(target)
    return jsonify(assets)


def _validate_asset_entry(entry: dict) -> tuple | None:
    """Validate a single asset entry from the request payload.

    Returns:
        None if valid, or a (response, status_code) tuple on error.
    """
    required = ["asset_id", "asset_name", "purpose", "target_ratio", "lower", "upper"]
    for field in required:
        if field not in entry:
            return jsonify({"error": f"Missing required field: '{field}'."}), 400

    if not isinstance(entry["asset_id"], str) or not entry["asset_id"]:
        return jsonify({"error": "'asset_id' must be a non-empty string."}), 400
    if not isinstance(entry["asset_name"], str) or not entry["asset_name"]:
        return jsonify({"error": "'asset_name' must be a non-empty string."}), 400
    if not isinstance(entry["purpose"], str) or not entry["purpose"]:
        return jsonify({"error": "'purpose' must be a non-empty string."}), 400

    for num_field in ("target_ratio", "lower", "upper"):
        val = entry[num_field]
        if not isinstance(val, (int, float)) or isinstance(val, bool):
            return jsonify({"error": f"'{num_field}' must be a number."}), 400

    return None


@target_bp.route("/<date>", methods=["PUT"])
def update_target(date: str):
    """Update an existing target allocation with full replacement.

    Expects JSON body with ``mode`` and ``assets`` fields.
    Mode determines save behavior:
    - ``"overwrite"``: replaces the original file, preserving its date.
    - ``"new"``: saves as a new target with today's date.

    Args:
        date: ISO date string (YYYY-MM-DD) of the target to update.

    Returns:
        200 with updated target DTO for overwrite mode,
        201 with new target DTO for new mode,
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

    assets = body.get("assets")
    if not assets or not isinstance(assets, list) or len(assets) == 0:
        return jsonify({"error": "'assets' must be a non-empty list."}), 400

    # Validate each asset entry
    for entry in assets:
        error = _validate_asset_entry(entry)
        if error is not None:
            return error

    # Verify the source target exists
    matching = list(path_mod.TARGETS_DIR.glob(f"target_{date}_v*.json"))
    if not matching:
        return jsonify({"error": f"Target for {date} not found."}), 404

    # Build the new target allocation
    target = init_target()
    for entry in assets:
        try:
            add_asset_to_target(
                target,
                entry["asset_id"],
                entry["asset_name"],
                entry["purpose"],
                float(entry["target_ratio"]),
                float(entry["lower"]),
                float(entry["upper"]),
            )
        except DuplicateAssetError:
            return (
                jsonify({"error": f"Duplicate asset_id '{entry['asset_id']}'."}),
                400,
            )
        except InvalidTargetRatioError:
            return (
                jsonify({"error": "target_ratio must be between 0.0 and 1.0."}),
                400,
            )
        except InvalidToleranceBoundsError as e:
            return jsonify({"error": f"Invalid tolerance bounds: {e}"}), 400

    # Check total ratio — warn but allow save
    warnings = []
    total = target.total_ratio()
    if abs(total - 1.0) > 1e-6:
        warnings.append(
            f"Total target ratio is {total:.4f}, expected 1.0. "
            "Consider adjusting ratios."
        )

    # Save based on mode
    dto = target_to_dto(target)
    if mode == "overwrite":
        latest_file = sorted(matching)[-1]
        save_target_overwrite(target, latest_file.name)
        result = {**dto, "warnings": warnings} if warnings else dto
        return jsonify(result), 200
    else:  # mode == "new"
        save_target(target)
        result = {**dto, "warnings": warnings} if warnings else dto
        return jsonify(result), 201
