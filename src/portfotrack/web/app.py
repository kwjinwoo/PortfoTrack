"""Flask application factory for PortfoTrack web UI.

Provides a local-only web interface backed by the existing services layer.
No external network calls; all data is read from and written to local
JSON files.
"""

from flask import Flask, jsonify, render_template


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

    from portfotrack.web.routes.report_routes import report_bp
    from portfotrack.web.routes.snapshot_routes import snapshot_bp
    from portfotrack.web.routes.target_routes import target_bp

    app.register_blueprint(snapshot_bp)
    app.register_blueprint(target_bp)
    app.register_blueprint(report_bp)

    return app
