"""Allocation report API routes.

Provides an endpoint for generating allocation comparison reports
by combining a snapshot with the latest target allocation.
"""

import re

from flask import Blueprint, jsonify, request

import portfotrack.path as path_mod
from portfotrack.services.allocation_report import generate_allocation_report
from portfotrack.services.target_services import load_latest_target
from portfotrack.storage.json_store.errors import SnapshotNotFoundError
from portfotrack.storage.json_store.snapshot_store import load as store_load
from portfotrack.storage.serialization.snapshot_json import dto_to_snapshot

_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")

report_bp = Blueprint("reports", __name__, url_prefix="/api/reports")


@report_bp.route("/allocation", methods=["GET"])
def allocation_report():
    """Generate an allocation comparison report.

    Query params:
        snapshot_date: ISO date string (YYYY-MM-DD) of the snapshot to use.

    Returns:
        JSON report with per-asset comparison data, or 400/404 error.
    """
    snapshot_date = request.args.get("snapshot_date")
    if not snapshot_date:
        return jsonify({"error": "Query parameter 'snapshot_date' is required."}), 400

    if not _DATE_PATTERN.match(snapshot_date):
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400

    # Load snapshot
    matching = list(path_mod.SNAPSHOTS_DIR.glob(f"snapshot_{snapshot_date}_v*.json"))
    if not matching:
        return jsonify({"error": f"Snapshot for {snapshot_date} not found."}), 404

    latest_file = sorted(matching)[-1]
    try:
        snapshot_dto = store_load(latest_file.name)
    except SnapshotNotFoundError:
        return jsonify({"error": f"Snapshot for {snapshot_date} not found."}), 404

    snapshot = dto_to_snapshot(snapshot_dto)

    # Load target
    try:
        target = load_latest_target()
    except FileNotFoundError:
        return jsonify({"error": "No target allocation found."}), 404

    # Generate report
    report = generate_allocation_report(target, snapshot)

    # Serialize report to JSON
    items = []
    for item in report.report_items:
        items.append(
            {
                "asset_id": item.asset_id,
                "asset_name": item.asset_name,
                "current_amount": item.current_amount,
                "total_portfolio": item.total_portfolio,
                "current_ratio": item.current_ratio,
                "target_ratio": item.target_ratio,
                "target_amount_needed": item.target_amount_needed,
                "tolerance": {
                    "lower": item.tolerance["lower"],
                    "upper": item.tolerance["upper"],
                },
                "is_within_tolerance": item.is_within_tolerance,
            }
        )

    return jsonify(
        {
            "snapshot_date": report.snapshot_date,
            "total_portfolio_amount": report.total_portfolio_amount,
            "is_complete": report.is_complete(),
            "total_additional_needed": report.total_additional_needed(),
            "items": items,
        }
    )
