"""Allocation report API routes.

Provides an endpoint for generating allocation comparison reports
by combining a snapshot with the latest target allocation.
"""

import re

from flask import Blueprint, Response, jsonify, request

from portfotrack.services.allocation_context_export import (
    build_allocation_context_export,
)
from portfotrack.services.chatgpt_export import format_portfolio_markdown
from portfotrack.services.report_services import (
    AllocationReportContext,
    load_allocation_report_context,
)
from portfotrack.storage.json_store.errors import SnapshotNotFoundError

_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")

report_bp = Blueprint("reports", __name__, url_prefix="/api/reports")


def _validated_snapshot_date() -> str | tuple[Response, int]:
    snapshot_date = request.args.get("snapshot_date")
    if not snapshot_date:
        return jsonify({"error": "Query parameter 'snapshot_date' is required."}), 400
    if not _DATE_PATTERN.match(snapshot_date):
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400
    return snapshot_date


def _load_context(
    snapshot_date: str,
) -> AllocationReportContext | tuple[Response, int]:
    try:
        return load_allocation_report_context(snapshot_date)
    except SnapshotNotFoundError:
        return jsonify({"error": f"Snapshot for {snapshot_date} not found."}), 404
    except FileNotFoundError:
        return jsonify({"error": "No target allocation found."}), 404


@report_bp.route("/allocation", methods=["GET"])
def allocation_report():
    """Generate an allocation comparison report.

    Query params:
        snapshot_date: ISO date string (YYYY-MM-DD) of the snapshot to use.

    Returns:
        JSON report with per-asset comparison data, or 400/404 error.
    """
    snapshot_date = _validated_snapshot_date()
    if not isinstance(snapshot_date, str):
        return snapshot_date
    context = _load_context(snapshot_date)
    if not isinstance(context, AllocationReportContext):
        return context
    report = context.report

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


@report_bp.route("/allocation/export", methods=["GET"])
def allocation_markdown_export():
    """Export a snapshot and the latest target as a Markdown attachment.

    Query params:
        snapshot_date: ISO date string (YYYY-MM-DD) of the snapshot to use.
        include_labels: ``false`` omits individual holding labels.
        hide_amounts: ``true`` omits exact monetary amounts.

    Returns:
        UTF-8 Markdown suitable for copying into a local AI conversation, or
        a JSON 400/404 response when the requested data is unavailable.
    """
    snapshot_date = _validated_snapshot_date()
    if not isinstance(snapshot_date, str):
        return snapshot_date
    context = _load_context(snapshot_date)
    if not isinstance(context, AllocationReportContext):
        return context
    markdown = format_portfolio_markdown(
        context.target,
        context.snapshot,
        context.report,
        include_labels=request.args.get("include_labels", "true").lower() != "false",
        hide_amounts=request.args.get("hide_amounts", "false").lower() == "true",
    )
    return Response(
        markdown,
        mimetype="text/markdown",
        headers={
            "Content-Disposition": (
                f'attachment; filename="portfotrack-{snapshot_date}.md"'
            )
        },
    )


@report_bp.route("/allocation/export.json", methods=["GET"])
def allocation_context_export():
    """Download versioned allocation facts for an explicit snapshot.

    Query params:
        snapshot_date: Required ISO date string (YYYY-MM-DD).

    Returns:
        A local JSON attachment, or a JSON 400/404 response when the requested
        portfolio context is unavailable.
    """
    snapshot_date = _validated_snapshot_date()
    if not isinstance(snapshot_date, str):
        return snapshot_date
    context = _load_context(snapshot_date)
    if not isinstance(context, AllocationReportContext):
        return context
    response = jsonify(
        build_allocation_context_export(context.snapshot, context.report)
    )
    response.headers["Content-Disposition"] = (
        f'attachment; filename="portfotrack-allocation-{snapshot_date}-v1.json"'
    )
    return response
