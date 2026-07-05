"""Optional bet API routes.

Provides endpoints for listing, retrieving, creating, and managing
optional bet snapshots. All endpoints delegate to the services layer;
no domain logic is performed here.
"""

from flask import Blueprint, jsonify, request

import portfotrack.path as path_mod
from portfotrack.domain.optional_bet.errors import (
    DuplicateOptionalBetError,
    InvalidCapRatioError,
    OptionalBetAssetNotFoundError,
)
from portfotrack.services.optional_bet_services import (
    add_item,
    check_cap_breaches_with_snapshot,
    init_optional_bet_snapshot,
    load_all_optional_bets,
    load_latest_optional_bet,
    load_optional_bet_by_filename,
    record_today_amounts,
    remove_item,
    save_optional_bet,
    save_optional_bet_overwrite,
    update_item,
)
from portfotrack.services.optional_bet_trend_analysis import (
    compute_optional_bet_trend,
)
from portfotrack.storage.json_store.errors import (
    OptionalBetNotFoundError,
    SnapshotNotFoundError,
)
from portfotrack.storage.serialization.optional_bet_json import optional_bet_to_dto
from portfotrack.web.date_validation import is_iso_date

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


@optional_bet_bp.route("/trends/analysis", methods=["GET"])
def trend_analysis():
    """Generate trend analysis data from all optional bet snapshots.

    Returns:
        JSON response with asset_trends, portfolio_trend, and metadata.
    """
    snapshots = load_all_optional_bets()
    portfolio_trend = compute_optional_bet_trend(snapshots)

    # Serialize asset trends
    asset_trends_json = []
    for at in portfolio_trend.asset_trends:
        data_points = [
            {"date": dp.date, "amount": dp.amount, "ratio": dp.ratio}
            for dp in at.data_points
        ]
        asset_trends_json.append(
            {
                "asset_id": at.asset_id,
                "asset_name": at.asset_name,
                "data_points": data_points,
            }
        )

    # Serialize portfolio total trend
    portfolio_trend_json = [
        {
            "date": tp.date,
            "total_amount": tp.total_amount,
            "change_pct": tp.change_pct,
        }
        for tp in portfolio_trend.total_data_points
    ]

    # Build metadata
    dates = [tp.date for tp in portfolio_trend.total_data_points]
    metadata = {
        "snapshot_count": len(snapshots),
        "asset_count": len(portfolio_trend.asset_trends),
        "start_date": dates[0] if dates else None,
        "end_date": dates[-1] if dates else None,
    }

    return jsonify(
        {
            "asset_trends": asset_trends_json,
            "portfolio_trend": portfolio_trend_json,
            "metadata": metadata,
        }
    )


@optional_bet_bp.route("", methods=["POST"])
def create_optional_bet():
    """Create and persist a new optional bet snapshot.

    Expects JSON body with an ``items`` list (may be empty).
    Each item must have ``asset_id``, ``name``, ``cap_ratio``, ``amount``.

    Returns:
        201 with the created snapshot DTO, or 400/409 on validation failure.
    """
    body = request.get_json(silent=True)
    if body is None:
        return jsonify({"error": "Request body must be valid JSON."}), 400

    items = body.get("items")
    if items is None or not isinstance(items, list):
        return jsonify({"error": "'items' must be a list."}), 400

    if items:
        error_resp = _validate_items(items)
        if error_resp is not None:
            return error_resp

    snapshot = init_optional_bet_snapshot()
    for item in items:
        try:
            add_item(
                snapshot,
                item["asset_id"],
                item["name"],
                float(item["cap_ratio"]),
                int(item["amount"]),
            )
        except DuplicateOptionalBetError:
            return (
                jsonify({"error": f"Duplicate asset_id '{item['asset_id']}'."}),
                409,
            )
        except InvalidCapRatioError:
            return (
                jsonify(
                    {"error": "cap_ratio must be between 0.0 and 1.0 (exclusive)."}
                ),
                400,
            )

    save_optional_bet(snapshot)
    dto = optional_bet_to_dto(snapshot)
    return jsonify(dto), 201


@optional_bet_bp.route("/items", methods=["POST"])
def add_item_route():
    """Add an item to the latest optional bet snapshot.

    Expects JSON body with ``asset_id``, ``name``, ``cap_ratio``, ``amount``.

    Returns:
        200 with updated snapshot DTO, or 400/404/409 on error.
    """
    body = request.get_json(silent=True)
    if body is None:
        return jsonify({"error": "Request body must be valid JSON."}), 400

    error_resp = _validate_single_item(body)
    if error_resp is not None:
        return error_resp

    try:
        snapshot = load_latest_optional_bet()
    except OptionalBetNotFoundError:
        return jsonify({"error": "No optional bet snapshot found."}), 404

    try:
        add_item(
            snapshot,
            body["asset_id"],
            body["name"],
            float(body["cap_ratio"]),
            int(body["amount"]),
        )
    except DuplicateOptionalBetError:
        return (
            jsonify({"error": f"Asset '{body['asset_id']}' already exists."}),
            409,
        )
    except InvalidCapRatioError:
        return (
            jsonify({"error": "cap_ratio must be between 0.0 and 1.0 (exclusive)."}),
            400,
        )

    _save_latest(snapshot)
    dto = optional_bet_to_dto(snapshot)
    return jsonify(dto)


@optional_bet_bp.route("/items/<asset_id>", methods=["DELETE"])
def remove_item_route(asset_id: str):
    """Remove an item from the latest optional bet snapshot.

    Args:
        asset_id: Identifier of the item to remove.

    Returns:
        200 with updated snapshot DTO, or 404 if not found.
    """
    try:
        snapshot = load_latest_optional_bet()
    except OptionalBetNotFoundError:
        return jsonify({"error": "No optional bet snapshot found."}), 404

    try:
        remove_item(snapshot, asset_id)
    except OptionalBetAssetNotFoundError:
        return jsonify({"error": f"Asset '{asset_id}' not found."}), 404

    _save_latest(snapshot)
    dto = optional_bet_to_dto(snapshot)
    return jsonify(dto)


@optional_bet_bp.route("/items/<asset_id>", methods=["PATCH"])
def update_item_route(asset_id: str):
    """Update fields of an item in the latest optional bet snapshot.

    Accepts partial updates: ``name``, ``cap_ratio``, ``amount``.

    Args:
        asset_id: Identifier of the item to update.

    Returns:
        200 with updated snapshot DTO, or 400/404 on error.
    """
    body = request.get_json(silent=True)
    if body is None:
        return jsonify({"error": "Request body must be valid JSON."}), 400

    try:
        snapshot = load_latest_optional_bet()
    except OptionalBetNotFoundError:
        return jsonify({"error": "No optional bet snapshot found."}), 404

    name = body.get("name")
    cap_ratio = body.get("cap_ratio")
    amount = body.get("amount")

    if cap_ratio is not None:
        cap_ratio = float(cap_ratio)
    if amount is not None:
        amount = int(amount)

    try:
        update_item(snapshot, asset_id, name=name, cap_ratio=cap_ratio, amount=amount)
    except OptionalBetAssetNotFoundError:
        return jsonify({"error": f"Asset '{asset_id}' not found."}), 404
    except InvalidCapRatioError:
        return (
            jsonify({"error": "cap_ratio must be between 0.0 and 1.0 (exclusive)."}),
            400,
        )

    _save_latest(snapshot)
    dto = optional_bet_to_dto(snapshot)
    return jsonify(dto)


@optional_bet_bp.route("/<date>", methods=["GET"])
def get_optional_bet_by_date(date: str):
    """Load an optional bet snapshot by date.

    Finds the latest version file matching the given date and returns
    its contents.

    Args:
        date: ISO date string (YYYY-MM-DD) of the snapshot.

    Returns:
        JSON representation of the snapshot, or 400/404 on error.
    """
    if not is_iso_date(date):
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400

    matching = sorted(path_mod.OPTIONAL_BETS_DIR.glob(f"optional_bet_{date}_v*.json"))
    if not matching:
        return (
            jsonify({"error": f"Optional bet for {date} not found."}),
            404,
        )

    latest_file = matching[-1]
    try:
        snapshot = load_optional_bet_by_filename(latest_file.name)
    except OptionalBetNotFoundError:
        return (
            jsonify({"error": f"Optional bet for {date} not found."}),
            404,
        )

    dto = optional_bet_to_dto(snapshot)
    return jsonify(dto)


@optional_bet_bp.route("/<date>", methods=["PUT"])
def update_optional_bet(date: str):
    """Update an existing optional bet snapshot with full replacement.

    Expects JSON body with ``mode`` and ``items`` fields.
    Mode determines save behavior:
    - ``"overwrite"``: replaces the original file, preserving its date.
    - ``"new"``: saves as a new snapshot with today's date.

    Args:
        date: ISO date string (YYYY-MM-DD) of the snapshot to update.

    Returns:
        200 with updated snapshot DTO for overwrite mode,
        201 with new snapshot DTO for new mode,
        or 400/404/409 on validation failure.
    """
    if not is_iso_date(date):
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
    if items is None or not isinstance(items, list):
        return jsonify({"error": "'items' must be a list."}), 400

    if items:
        error_resp = _validate_items(items)
        if error_resp is not None:
            return error_resp

    # Verify the source snapshot exists
    matching = list(path_mod.OPTIONAL_BETS_DIR.glob(f"optional_bet_{date}_v*.json"))
    if not matching:
        return (
            jsonify({"error": f"Optional bet for {date} not found."}),
            404,
        )

    # Build the new snapshot
    snapshot = init_optional_bet_snapshot()
    for item in items:
        try:
            add_item(
                snapshot,
                item["asset_id"],
                item["name"],
                float(item["cap_ratio"]),
                int(item["amount"]),
            )
        except DuplicateOptionalBetError:
            return (
                jsonify({"error": f"Duplicate asset_id '{item['asset_id']}'."}),
                409,
            )
        except InvalidCapRatioError:
            return (
                jsonify(
                    {"error": "cap_ratio must be between 0.0 and 1.0 (exclusive)."}
                ),
                400,
            )

    dto = optional_bet_to_dto(snapshot)
    if mode == "overwrite":
        snapshot.date = date
        latest_file = sorted(matching)[-1]
        save_optional_bet_overwrite(snapshot, latest_file.name)
        dto = optional_bet_to_dto(snapshot)
        return jsonify(dto), 200
    else:  # mode == "new"
        save_optional_bet(snapshot)
        return jsonify(dto), 201


@optional_bet_bp.route("/breaches", methods=["GET"])
def check_breaches():
    """Check which optional bet items exceed their cap ratios.

    Uses a portfolio snapshot to determine the main portfolio total.
    By default the latest snapshot is used; pass an explicit filename
    via the ``snapshot`` query parameter to use a specific one.

    Query parameters:
        snapshot: Optional snapshot filename (e.g.
            ``snapshot_2026-02-14_v1.json``).

    Returns:
        JSON object with ``breaches``, ``snapshot_date``, and
        ``main_portfolio_total``, or 404 on error.
    """
    snapshot_filename = request.args.get("snapshot")

    try:
        report = check_cap_breaches_with_snapshot(
            snapshot_filename=snapshot_filename,
        )
    except OptionalBetNotFoundError:
        return jsonify({"error": "No optional bet snapshot found."}), 404
    except SnapshotNotFoundError:
        return jsonify({"error": "No portfolio snapshot found."}), 404

    result = [
        {
            "asset_id": b.asset_id,
            "name": b.name,
            "actual_ratio": b.actual_ratio,
            "cap_ratio": b.cap_ratio,
        }
        for b in report["breaches"]
    ]
    return jsonify(
        {
            "breaches": result,
            "snapshot_date": report["snapshot_date"],
            "main_portfolio_total": report["main_portfolio_total"],
        }
    )


@optional_bet_bp.route("/record-today", methods=["POST"])
def record_today():
    """Record today's amounts for all optional bet items.

    Creates a new snapshot dated today with updated amounts.
    All asset_ids from the latest snapshot must be included.

    Expects JSON body with an ``items`` list where each item has
    ``asset_id`` (str) and ``amount`` (int).

    Returns:
        200 with the new snapshot DTO, or 400/404 on error.
    """
    body = request.get_json(silent=True)
    if body is None:
        return jsonify({"error": "Request body must be valid JSON."}), 400

    items = body.get("items")
    if items is None or not isinstance(items, list):
        return jsonify({"error": "'items' must be a list."}), 400

    for item in items:
        if not isinstance(item, dict):
            return jsonify({"error": "Each item must be an object."}), 400
        if "asset_id" not in item or "amount" not in item:
            return (
                jsonify({"error": "Each item must have 'asset_id' and 'amount'."}),
                400,
            )
        if not isinstance(item["asset_id"], str) or not item["asset_id"]:
            return (
                jsonify({"error": "'asset_id' must be a non-empty string."}),
                400,
            )
        if not isinstance(item["amount"], int) or isinstance(item["amount"], bool):
            return jsonify({"error": "'amount' must be an integer."}), 400

    try:
        latest = load_latest_optional_bet()
    except OptionalBetNotFoundError:
        return jsonify({"error": "No optional bet snapshot found."}), 404

    amount_updates = {item["asset_id"]: item["amount"] for item in items}

    try:
        new_snapshot = record_today_amounts(latest, amount_updates)
    except OptionalBetAssetNotFoundError as e:
        return jsonify({"error": str(e)}), 400
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    save_optional_bet(new_snapshot)
    dto = optional_bet_to_dto(new_snapshot)
    return jsonify(dto)


def _validate_items(items: list) -> tuple | None:
    """Validate a list of item dicts for required fields.

    Returns:
        None if valid, or (error_response, status_code) tuple if invalid.
    """
    for item in items:
        error_resp = _validate_single_item(item)
        if error_resp is not None:
            return error_resp
    return None


def _validate_single_item(item: dict) -> tuple | None:
    """Validate a single item dict for required fields and types.

    Returns:
        None if valid, or (error_response, status_code) tuple if invalid.
    """
    if not isinstance(item, dict):
        return jsonify({"error": "Each item must be an object."}), 400

    for field in ("asset_id", "name", "cap_ratio", "amount"):
        if field not in item:
            return (
                jsonify(
                    {
                        "error": f"Missing required field: '{field}'.",
                    }
                ),
                400,
            )

    if not isinstance(item["asset_id"], str) or not item["asset_id"]:
        return jsonify({"error": "'asset_id' must be a non-empty string."}), 400
    if not isinstance(item["name"], str) or not item["name"]:
        return jsonify({"error": "'name' must be a non-empty string."}), 400
    if not isinstance(item["cap_ratio"], (int, float)) or isinstance(
        item["cap_ratio"], bool
    ):
        return jsonify({"error": "'cap_ratio' must be a number."}), 400
    if not isinstance(item["amount"], int) or isinstance(item["amount"], bool):
        return jsonify({"error": "'amount' must be an integer."}), 400

    return None


def _save_latest(snapshot) -> None:
    """Save the snapshot back to the latest file (overwrite).

    Finds the latest file for the snapshot's date and overwrites it.
    Falls back to creating a new file if none exists.
    """
    matching = list(
        path_mod.OPTIONAL_BETS_DIR.glob(f"optional_bet_{snapshot.date}_v*.json")
    )
    if matching:
        latest_file = sorted(matching)[-1]
        save_optional_bet_overwrite(snapshot, latest_file.name)
    else:
        save_optional_bet(snapshot)
