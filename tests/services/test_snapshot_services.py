from datetime import date

from portfotrack.domain.snapshot import Snapshot
from portfotrack.services.snapshot_services import (
    add_item_to_snapshot,
    aggregate_snapshot,
    init_snapshot,
)


class TestInitSnapshot:
    """Tests for init_snapshot function."""

    def test_returns_empty_snapshot(self):
        """init_snapshot should return a new Snapshot with no items."""
        snapshot = init_snapshot()

        assert isinstance(snapshot, Snapshot)
        assert snapshot.items == []
        assert snapshot.currency == "KRW"
        assert snapshot.date == date.today().isoformat()


class TestAddItemToSnapshot:
    """Tests for add_item_to_snapshot function."""

    def test_adds_single_item_and_returns_same_instance(self):
        """add_item_to_snapshot should mutate snapshot and return same instance."""
        snapshot = Snapshot()

        result = add_item_to_snapshot(snapshot, "US_EQUITY", "S&P500", 100000)

        assert result is snapshot
        assert len(snapshot.items) == 1
        assert snapshot.items[0].asset_id == "US_EQUITY"
        assert snapshot.items[0].label == "S&P500"
        assert snapshot.items[0].amount == 100000

    def test_adds_multiple_items_sequentially(self):
        """Multiple calls should accumulate items in the snapshot."""
        snapshot = Snapshot()

        add_item_to_snapshot(snapshot, "US_EQUITY", "S&P500", 100000)
        add_item_to_snapshot(snapshot, "KR_BOND", "Treasury", 50000)
        add_item_to_snapshot(snapshot, "US_EQUITY", "Nasdaq100", 30000)

        assert len(snapshot.items) == 3
        assert snapshot.items[0].asset_id == "US_EQUITY"
        assert snapshot.items[1].asset_id == "KR_BOND"
        assert snapshot.items[2].asset_id == "US_EQUITY"

    def test_allows_zero_amount(self):
        """Zero amounts should be valid for tracking holdings with no value."""
        snapshot = Snapshot()

        result = add_item_to_snapshot(snapshot, "CASH", "Empty_Account", 0)

        assert result is snapshot
        assert len(snapshot.items) == 1
        assert snapshot.items[0].amount == 0


class TestAggregateSnapshot:
    """Tests for aggregate_snapshot function."""

    def test_empty_snapshot_returns_empty_dict(self):
        """aggregate_snapshot should return empty dict for snapshot with no items."""
        snapshot = Snapshot()

        result = aggregate_snapshot(snapshot)

        assert result == {}

    def test_single_item_returns_one_entry(self):
        """Snapshot with one item should return dict with one asset_id entry."""
        snapshot = Snapshot()
        snapshot.add_snapshot_item("US_EQUITY", "S&P500", 100000)

        result = aggregate_snapshot(snapshot)

        assert result == {"US_EQUITY": 100000}

    def test_multiple_items_same_asset_id_are_summed(self):
        """Items with same asset_id should be aggregated into one total."""
        snapshot = Snapshot()
        snapshot.add_snapshot_item("US_EQUITY", "S&P500", 100000)
        snapshot.add_snapshot_item("US_EQUITY", "Nasdaq100", 50000)
        snapshot.add_snapshot_item("US_EQUITY", "Tech_ETF", 25000)

        result = aggregate_snapshot(snapshot)

        assert result == {"US_EQUITY": 175000}

    def test_multiple_different_asset_ids(self):
        """Different asset_ids should produce separate totals."""
        snapshot = Snapshot()
        snapshot.add_snapshot_item("US_EQUITY", "S&P500", 100000)
        snapshot.add_snapshot_item("KR_BOND", "Treasury", 50000)
        snapshot.add_snapshot_item("CASH", "Savings", 30000)

        result = aggregate_snapshot(snapshot)

        assert result == {
            "US_EQUITY": 100000,
            "KR_BOND": 50000,
            "CASH": 30000,
        }

    def test_mixed_asset_ids_with_duplication(self):
        """Complex scenario with multiple items per asset_id."""
        snapshot = Snapshot()
        snapshot.add_snapshot_item("US_EQUITY", "S&P500", 100000)
        snapshot.add_snapshot_item("KR_BOND", "Treasury", 50000)
        snapshot.add_snapshot_item("US_EQUITY", "Nasdaq100", 30000)
        snapshot.add_snapshot_item("CASH", "Savings", 20000)
        snapshot.add_snapshot_item("KR_BOND", "Corporate", 10000)

        result = aggregate_snapshot(snapshot)

        assert result == {
            "US_EQUITY": 130000,
            "KR_BOND": 60000,
            "CASH": 20000,
        }

    def test_zero_amounts_included_in_aggregation(self):
        """Zero amounts should be included in the aggregation."""
        snapshot = Snapshot()
        snapshot.add_snapshot_item("US_EQUITY", "S&P500", 100000)
        snapshot.add_snapshot_item("US_EQUITY", "Empty", 0)
        snapshot.add_snapshot_item("CASH", "Zero_Balance", 0)

        result = aggregate_snapshot(snapshot)

        assert result == {
            "US_EQUITY": 100000,
            "CASH": 0,
        }
