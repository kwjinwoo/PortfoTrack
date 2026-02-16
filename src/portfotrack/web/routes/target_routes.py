"""Target allocation API routes.

Provides endpoints for loading, creating, and managing target allocations.
All endpoints delegate to the services layer.
"""

from flask import Blueprint, jsonify, request

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
)
from portfotrack.storage.serialization.target_json import target_to_dto

target_bp = Blueprint("targets", __name__, url_prefix="/api/targets")


@target_bp.route("", methods=["GET"])
def get_target():
    """Load the latest target allocation.

    Returns:
        JSON representation of the target allocation, or 404 if none exists.
    """
    try:
        target = load_latest_target()
    except FileNotFoundError:
        return jsonify({"error": "No target allocation found."}), 404

    dto = target_to_dto(target)
    return jsonify(dto)


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
