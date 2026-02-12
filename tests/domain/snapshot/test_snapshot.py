import datetime

from portfotrack.domain.snapshot.snapshot import Snapshot, SnapshotItem


class TestSnapshotItemEquality:
    """Tests for SnapshotItem __eq__ behavior."""

    def test_equal_when_same_asset_id_and_label(self):
        """Two SnapshotItems with same asset_id and label are equal, regardless of amount."""
        item_a = SnapshotItem(asset_id="us_equity", label="S&P500", amount=100)
        item_b = SnapshotItem(asset_id="us_equity", label="S&P500", amount=999)

        assert item_a == item_b

    def test_not_equal_when_different_asset_id(self):
        """SnapshotItems with different asset_id are not equal."""
        item_a = SnapshotItem(asset_id="us_equity", label="S&P500", amount=100)
        item_b = SnapshotItem(asset_id="kr_equity", label="S&P500", amount=100)

        assert item_a != item_b

    def test_not_equal_when_different_label(self):
        """SnapshotItems with same asset_id but different label are not equal."""
        item_a = SnapshotItem(asset_id="us_equity", label="S&P500", amount=100)
        item_b = SnapshotItem(asset_id="us_equity", label="Nasdaq100", amount=100)

        assert item_a != item_b

    def test_not_equal_to_non_snapshot_item(self):
        """SnapshotItem is not equal to objects of other types."""
        item = SnapshotItem(asset_id="us_equity", label="S&P500", amount=100)

        assert item != "not_a_snapshot_item"
        assert item != 42


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

    def test_add_duplicate_asset_id_with_different_label_kept_separate(self):
        """Items with same asset_id but different labels remain separate."""
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

    def test_add_same_asset_id_and_label_merges_amount(self):
        """Adding an item with same asset_id and label should merge amounts."""
        snapshot = Snapshot()
        snapshot.add_snapshot_item(asset_id="us_equity", label="S&P500", amount=100)
        snapshot.add_snapshot_item(asset_id="us_equity", label="S&P500", amount=50)

        assert len(snapshot.items) == 1
        assert snapshot.items[0].amount == 150

    def test_add_same_item_three_times_accumulates(self):
        """Repeated adds of same asset_id and label accumulate amounts."""
        snapshot = Snapshot()
        snapshot.add_snapshot_item(asset_id="us_equity", label="S&P500", amount=100)
        snapshot.add_snapshot_item(asset_id="us_equity", label="S&P500", amount=50)
        snapshot.add_snapshot_item(asset_id="us_equity", label="S&P500", amount=30)

        assert len(snapshot.items) == 1
        assert snapshot.items[0].amount == 180

    def test_merge_and_separate_items_mixed(self):
        """Merge applies only to matching asset_id+label; others stay separate.

        Scenario: user adds us_equity S&P500 from two brokers, plus distinct
        items for Nasdaq100 and kr_bond. Only S&P500 should be merged.
        """
        snapshot = Snapshot()
        snapshot.add_snapshot_item(asset_id="us_equity", label="S&P500", amount=100)
        snapshot.add_snapshot_item(asset_id="us_equity", label="Nasdaq100", amount=200)
        snapshot.add_snapshot_item(asset_id="kr_bond", label="KTB", amount=300)
        snapshot.add_snapshot_item(asset_id="us_equity", label="S&P500", amount=50)

        assert len(snapshot.items) == 3
        assert snapshot.items[0].amount == 150  # S&P500 merged
        assert snapshot.items[1].amount == 200  # Nasdaq100 untouched
        assert snapshot.items[2].amount == 300  # KTB untouched

    def test_user_scenario_two_brokers_same_holding(self):
        """Real-world scenario: same stock held across two brokerage accounts.

        User has us_equity S&P500 at broker A (100) and discovers broker B
        also holds 50. After two add_snapshot_item calls, the single merged
        item should have amount 150.
        """
        snapshot = Snapshot()
        # Broker A
        snapshot.add_snapshot_item(asset_id="us_equity", label="S&P500", amount=100)
        # Broker B (discovered later)
        snapshot.add_snapshot_item(asset_id="us_equity", label="S&P500", amount=50)

        assert len(snapshot.items) == 1
        assert snapshot.items[0].asset_id == "us_equity"
        assert snapshot.items[0].label == "S&P500"
        assert snapshot.items[0].amount == 150
