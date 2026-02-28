"""Tests for target allocation UI page content.

Verifies that the targets page contains the expected HTML structure
(form elements, table structure, JS references) needed for the UI.
"""

import pytest


@pytest.fixture()
def client():
    """Create a test client for the Flask app."""
    from portfotrack.web.app import create_app

    app = create_app({"TESTING": True})
    return app.test_client()


class TestTargetsPageStructure:
    """Targets page should contain UI elements for management."""

    def test_contains_target_table(self, client):
        """Page should have a target assets table."""
        response = client.get("/targets")
        html = response.data.decode("utf-8")

        assert 'id="target-table"' in html
        assert 'id="target-assets"' in html

    def test_contains_create_button(self, client):
        """Page should have a create target button."""
        response = client.get("/targets")
        html = response.data.decode("utf-8")

        assert 'id="create-target-btn"' in html

    def test_contains_add_asset_form(self, client):
        """Page should have a form to add assets."""
        response = client.get("/targets")
        html = response.data.decode("utf-8")

        assert 'id="add-asset-form"' in html
        assert 'name="asset_id"' in html
        assert 'name="asset_name"' in html
        assert 'name="purpose"' in html
        assert 'name="target_ratio"' in html
        assert 'name="lower"' in html
        assert 'name="upper"' in html

    def test_references_targets_js(self, client):
        """Page should reference the targets UI script."""
        response = client.get("/targets")
        html = response.data.decode("utf-8")

        assert "targets-ui.js" in html

    def test_targets_js_accessible(self, client):
        """The targets-ui.js file should be accessible."""
        response = client.get("/static/js/targets-ui.js")

        assert response.status_code == 200

    def test_form_grid_layout(self, client):
        """Page should use form-grid class for layout."""
        response = client.get("/targets")
        html = response.data.decode("utf-8")

        assert "form-grid" in html


class TestTargetEditUI:
    """Targets page should contain UI elements for editing target allocations."""

    def test_contains_edit_card(self, client):
        """Page should have an edit target card."""
        response = client.get("/targets")
        html = response.data.decode("utf-8")

        assert 'id="target-edit-card"' in html

    def test_edit_card_has_assets_container(self, client):
        """Edit card should have a container for editable assets."""
        response = client.get("/targets")
        html = response.data.decode("utf-8")

        assert 'id="edit-assets-container"' in html

    def test_edit_card_has_add_asset_button(self, client):
        """Edit card should have a button to add new assets."""
        response = client.get("/targets")
        html = response.data.decode("utf-8")

        assert 'id="edit-add-asset-btn"' in html

    def test_edit_card_has_save_mode_selector(self, client):
        """Edit card should have radio buttons for save mode selection."""
        response = client.get("/targets")
        html = response.data.decode("utf-8")

        assert 'name="target-save-mode"' in html
        assert 'value="overwrite"' in html
        assert 'value="new"' in html

    def test_edit_card_has_save_button(self, client):
        """Edit card should have a save button."""
        response = client.get("/targets")
        html = response.data.decode("utf-8")

        assert 'id="edit-target-save-btn"' in html

    def test_edit_card_has_message_area(self, client):
        """Edit card should have a message display area."""
        response = client.get("/targets")
        html = response.data.decode("utf-8")

        assert 'id="edit-target-message"' in html
