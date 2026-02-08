import datetime

from portfotrack.domain.snapshot.snapshot import Snapshot


class TestSnapshot:
    """Tests for Snapshot class."""

    def test_snapshot_date_auto_set_to_today(self):
        """Snapshot date should be automatically set to today on creation."""
        snapshot = Snapshot()
        expected_date = datetime.date.today().isoformat()

        assert snapshot.date == expected_date

    def test_snapshot_default_currency_is_krw(self):
        """Snapshot currency should default to KRW."""
        snapshot = Snapshot()

        assert snapshot.currency == "KRW"

    def test_snapshot_items_initialized_as_empty_list(self):
        """Snapshot items should be initialized as an empty list."""
        snapshot = Snapshot()

        assert snapshot.items == []
        assert isinstance(snapshot.items, list)

    def test_add_single_snapshot_item(self):
        """add_snapshot_item should add a single item to the snapshot."""
        snapshot = Snapshot()
        snapshot.add_snapshot_item(asset_id="us_equity", label="S&P500", amount=1000000)

        assert len(snapshot.items) == 1
        assert snapshot.items[0].asset_id == "us_equity"
        assert snapshot.items[0].label == "S&P500"
        assert snapshot.items[0].amount == 1000000

    def test_add_multiple_snapshot_items(self):
        """add_snapshot_item should allow adding multiple items sequentially."""
        snapshot = Snapshot()
        snapshot.add_snapshot_item(asset_id="us_equity", label="S&P500", amount=1000000)
        snapshot.add_snapshot_item(asset_id="kr_bond", label="KTB", amount=500000)
        snapshot.add_snapshot_item(asset_id="cash", label="KRW Cash", amount=300000)

        assert len(snapshot.items) == 3
        assert snapshot.items[0].asset_id == "us_equity"
        assert snapshot.items[1].asset_id == "kr_bond"
        assert snapshot.items[2].asset_id == "cash"

    def test_add_duplicate_asset_id_allowed(self):
        """add_snapshot_item should allow multiple items with the same asset_id."""
        snapshot = Snapshot()
        snapshot.add_snapshot_item(asset_id="us_equity", label="S&P500", amount=1000000)
        snapshot.add_snapshot_item(
            asset_id="us_equity", label="Nasdaq100", amount=800000
        )

        assert len(snapshot.items) == 2
        assert snapshot.items[0].asset_id == "us_equity"
        assert snapshot.items[1].asset_id == "us_equity"
        assert snapshot.items[0].label == "S&P500"
        assert snapshot.items[1].label == "Nasdaq100"
