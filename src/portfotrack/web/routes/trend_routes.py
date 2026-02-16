"""Trend analysis API routes.

Provides an endpoint for retrieving portfolio trend data
computed from all available snapshots.
"""

from flask import Blueprint, jsonify

from portfotrack.services.trend_analysis import (
    compute_portfolio_trend,
    load_all_snapshots,
)

trend_bp = Blueprint("trends", __name__, url_prefix="/api/trends")


@trend_bp.route("/analysis", methods=["GET"])
def trend_analysis():
    """Generate trend analysis data from all snapshots.

    Returns:
        JSON response with asset_trends, portfolio_trend, and metadata.
    """
    snapshots = load_all_snapshots()
    portfolio_trend = compute_portfolio_trend(snapshots)

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
        {"date": tp.date, "total_amount": tp.total_amount}
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
