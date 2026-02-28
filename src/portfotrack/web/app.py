"""Flask application factory for PortfoTrack web UI.

Provides a local-only web interface backed by the existing services layer.
No external network calls; all data is read from and written to local
JSON files.
"""

import argparse
import sys

from flask import Flask, jsonify, render_template

_DEFAULT_HOST = "127.0.0.1"
_DEFAULT_PORT = 5000


def create_app(test_config: dict | None = None) -> Flask:
    """Create and configure the Flask application.

    Args:
        test_config: Optional configuration overrides.
            Typically used in tests to set TESTING=True.

    Returns:
        A configured Flask application instance.
    """
    app = Flask(__name__)

    if test_config is not None:
        app.config.update(test_config)

    @app.route("/health")
    def health():
        """Return a simple health-check response."""
        return jsonify({"status": "ok"})

    @app.route("/")
    def index():
        """Render the main dashboard page."""
        return render_template("index.html")

    @app.route("/snapshots")
    def snapshots_page():
        """Render the snapshots management page."""
        return render_template("snapshots.html")

    @app.route("/targets")
    def targets_page():
        """Render the target allocation management page."""
        return render_template("targets.html")

    @app.route("/reports")
    def reports_page():
        """Render the allocation report page."""
        return render_template("reports.html")

    @app.route("/trends")
    def trends_page():
        """Render the trend analysis page."""
        return render_template("trends.html")

    from portfotrack.web.routes.report_routes import report_bp
    from portfotrack.web.routes.snapshot_routes import snapshot_bp
    from portfotrack.web.routes.target_routes import target_bp
    from portfotrack.web.routes.trend_routes import trend_bp

    app.register_blueprint(snapshot_bp)
    app.register_blueprint(target_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(trend_bp)

    return app


def run_server(argv: list[str] | None = None) -> None:
    """Parse CLI arguments and start the Flask development server.

    Args:
        argv: Command-line arguments to parse. Defaults to sys.argv[1:]
            when None. Accepts --host and --port options.
    """
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(
        prog="portfotrack",
        description="Start the PortfoTrack web server.",
    )
    parser.add_argument(
        "--host",
        default=_DEFAULT_HOST,
        help=f"Host to bind to (default: {_DEFAULT_HOST})",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=_DEFAULT_PORT,
        help=f"Port to bind to (default: {_DEFAULT_PORT})",
    )
    args = parser.parse_args(argv)

    app = create_app()
    app.run(host=args.host, port=args.port, debug=False)
