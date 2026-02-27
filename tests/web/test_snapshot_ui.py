"""Tests for snapshot UI page content.

Verifies that the snapshots page contains the expected HTML structure
(form elements, table structure, JS references) needed for the UI.
"""

import pytest


@pytest.fixture()
def client():
    """Create a test client for the Flask app."""
    from portfotrack.web.app import create_app

    app = create_app({"TESTING": True})
    return app.test_client()


class TestSnapshotsPageStructure:
    """Snapshot page should contain UI elements for management."""

    def test_contains_snapshot_table(self, client):
        """Page should have a snapshot list table."""
        response = client.get("/snapshots")
        html = response.data.decode("utf-8")

        assert 'id="snapshot-table"' in html
        assert 'id="snapshot-list"' in html

    def test_contains_create_form(self, client):
        """Page should have a create snapshot form."""
        response = client.get("/snapshots")
        html = response.data.decode("utf-8")

        assert 'id="create-snapshot-form"' in html
        assert 'name="asset_id"' in html
        assert 'name="label"' in html
        assert 'name="amount"' in html

    def test_contains_add_item_button(self, client):
        """Page should have a button to add more items."""
        response = client.get("/snapshots")
        html = response.data.decode("utf-8")

        assert 'id="add-item-btn"' in html

    def test_references_snapshots_js(self, client):
        """Page should reference the snapshots UI script."""
        response = client.get("/snapshots")
        html = response.data.decode("utf-8")

        assert "snapshots-ui.js" in html

    def test_snapshots_js_accessible(self, client):
        """The snapshots-ui.js file should be accessible."""
        response = client.get("/static/js/snapshots-ui.js")

        assert response.status_code == 200

    def test_contains_asset_select_dropdown(self, client):
        """Page should have a select dropdown for asset_id."""
        response = client.get("/snapshots")
        html = response.data.decode("utf-8")

        assert 'name="asset_id"' in html
        assert "<select" in html

    def test_contains_no_target_warning(self, client):
        """Page should have a warning element for missing target."""
        response = client.get("/snapshots")
        html = response.data.decode("utf-8")

        assert 'id="no-target-warning"' in html


class TestSnapshotEditUI:
    """Snapshot page should contain UI elements for editing snapshots."""

    def test_contains_edit_card(self, client):
        """Page should have an edit snapshot card."""
        response = client.get("/snapshots")
        html = response.data.decode("utf-8")

        assert 'id="snapshot-edit-card"' in html

    def test_edit_card_has_items_container(self, client):
        """Edit card should have a container for editable items."""
        response = client.get("/snapshots")
        html = response.data.decode("utf-8")

        assert 'id="edit-items-container"' in html

    def test_edit_card_has_add_item_button(self, client):
        """Edit card should have a button to add new items."""
        response = client.get("/snapshots")
        html = response.data.decode("utf-8")

        assert 'id="edit-add-item-btn"' in html

    def test_edit_card_has_save_mode_selector(self, client):
        """Edit card should have radio buttons for save mode selection."""
        response = client.get("/snapshots")
        html = response.data.decode("utf-8")

        assert 'name="save-mode"' in html
        assert 'value="overwrite"' in html
        assert 'value="new"' in html

    def test_edit_card_has_save_button(self, client):
        """Edit card should have a save button."""
        response = client.get("/snapshots")
        html = response.data.decode("utf-8")

        assert 'id="edit-save-btn"' in html

    def test_edit_card_has_message_area(self, client):
        """Edit card should have a message display area."""
        response = client.get("/snapshots")
        html = response.data.decode("utf-8")

        assert 'id="edit-message"' in html
