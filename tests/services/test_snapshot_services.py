import json
from datetime import date

import pytest

from portfotrack.domain.snapshot import Snapshot
from portfotrack.services.snapshot_services import (
    add_item_to_snapshot,
    aggregate_snapshot,
    init_snapshot,
    load_latest_snapshot,
    load_snapshot_by_filename,
    remove_item_from_snapshot,
    replace_item_in_snapshot,
    save_snapshot,
    save_snapshot_overwrite,
)
from portfotrack.storage.json_store.errors import SnapshotNotFoundError


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


class TestSaveSnapshot:
    """Tests for save_snapshot function."""

    def test_saves_snapshot_with_single_item(self, tmp_path, monkeypatch):
        """save_snapshot should persist snapshot to JSON file."""
        from portfotrack.storage.json_store import snapshot_store

        monkeypatch.setattr(snapshot_store, "SNAPSHOTS_DIR", tmp_path)

        snapshot = Snapshot(date="2026-02-07", currency="KRW")
        snapshot.add_snapshot_item("US_EQUITY", "S&P500", 100000)

        save_snapshot(snapshot)

        # File name uses today's date (Asia/Seoul), not the snapshot's date
        files = list(tmp_path.glob("snapshot_*_v*.json"))
        assert len(files) == 1

    def test_saves_snapshot_with_multiple_items_in_order(self, tmp_path, monkeypatch):
        """save_snapshot should preserve item order."""
        from portfotrack.storage.json_store import snapshot_store

        monkeypatch.setattr(snapshot_store, "SNAPSHOTS_DIR", tmp_path)

        snapshot = Snapshot(date="2026-02-07")
        snapshot.add_snapshot_item("US_EQUITY", "S&P500", 100000)
        snapshot.add_snapshot_item("KR_BOND", "Treasury", 50000)
        snapshot.add_snapshot_item("US_EQUITY", "Nasdaq", 30000)

        save_snapshot(snapshot)

        files = list(tmp_path.glob("*.json"))
        with open(files[0]) as f:
            data = json.load(f)

        assert len(data["items"]) == 3
        assert data["items"][0]["label"] == "S&P500"
        assert data["items"][1]["label"] == "Treasury"
        assert data["items"][2]["label"] == "Nasdaq"

    def test_saves_empty_snapshot(self, tmp_path, monkeypatch):
        """save_snapshot should handle empty snapshot without items."""
        from portfotrack.storage.json_store import snapshot_store

        monkeypatch.setattr(snapshot_store, "SNAPSHOTS_DIR", tmp_path)

        snapshot = Snapshot()
        save_snapshot(snapshot)

        files = list(tmp_path.glob("*.json"))
        assert len(files) == 1


class TestLoadLatestSnapshot:
    """Tests for load_latest_snapshot function."""

    def test_loads_single_snapshot_when_only_one_exists(self, tmp_path, monkeypatch):
        """load_latest_snapshot should load the only snapshot if one exists."""
        from portfotrack import path as path_module
        from portfotrack.services import snapshot_services
        from portfotrack.storage.json_store import snapshot_store

        monkeypatch.setattr(path_module, "SNAPSHOTS_DIR", tmp_path)
        monkeypatch.setattr(snapshot_store, "SNAPSHOTS_DIR", tmp_path)
        monkeypatch.setattr(snapshot_services, "SNAPSHOTS_DIR", tmp_path)

        today = date.today().isoformat()
        snapshot = Snapshot(date=today)
        snapshot.add_snapshot_item("US_EQUITY", "S&P500", 100000)

        save_snapshot(snapshot)
        loaded = load_latest_snapshot()

        assert isinstance(loaded, Snapshot)
        assert loaded.date == today
        assert len(loaded.items) == 1
        assert loaded.items[0].asset_id == "US_EQUITY"
        assert loaded.items[0].amount == 100000

    def test_loads_latest_snapshot_from_multiple_dates(self, tmp_path, monkeypatch):
        """load_latest_snapshot should load newest by date sorting."""
        from portfotrack import path as path_module
        from portfotrack.services import snapshot_services
        from portfotrack.storage.json_store import snapshot_store

        monkeypatch.setattr(path_module, "SNAPSHOTS_DIR", tmp_path)
        monkeypatch.setattr(snapshot_store, "SNAPSHOTS_DIR", tmp_path)
        monkeypatch.setattr(snapshot_services, "SNAPSHOTS_DIR", tmp_path)

        # 2026-02-09 snapshot creation
        old_file = tmp_path / "snapshot_2026-02-09_v1.json"
        old_file.write_text(
            json.dumps(
                {
                    "date": "2026-02-09",
                    "currency": "KRW",
                    "items": [
                        {"asset_id": "CASH", "label": "OldCash", "amount": 50000}
                    ],
                },
                ensure_ascii=False,
            )
        )

        # 2026-02-10 snapshot creation
        mid_file = tmp_path / "snapshot_2026-02-10_v1.json"
        mid_file.write_text(
            json.dumps(
                {
                    "date": "2026-02-10",
                    "currency": "KRW",
                    "items": [
                        {"asset_id": "US_EQUITY", "label": "MidSnap", "amount": 100000}
                    ],
                },
                ensure_ascii=False,
            )
        )

        # 2026-02-11 snapshot creation (most recent)
        latest_snapshot = Snapshot(date="2026-02-11")
        latest_snapshot.add_snapshot_item("US_EQUITY", "LatestS&P500", 150000)
        save_snapshot(latest_snapshot)

        loaded = load_latest_snapshot()

        assert loaded.date == "2026-02-11"
        assert len(loaded.items) == 1
        assert loaded.items[0].label == "LatestS&P500"
        assert loaded.items[0].amount == 150000

    def test_raises_snapshot_not_found_when_no_file_exists(self, tmp_path, monkeypatch):
        """load_latest_snapshot should raise SnapshotNotFoundError if no snapshot."""
        from portfotrack import path as path_module
        from portfotrack.services import snapshot_services

        monkeypatch.setattr(path_module, "SNAPSHOTS_DIR", tmp_path)
        monkeypatch.setattr(snapshot_services, "SNAPSHOTS_DIR", tmp_path)

        with pytest.raises(SnapshotNotFoundError):
            load_latest_snapshot()

    def test_roundtrip_save_and_load_preserves_data(self, tmp_path, monkeypatch):
        """save then load sequence should preserve snapshot faithfully."""
        from portfotrack import path as path_module
        from portfotrack.services import snapshot_services
        from portfotrack.storage.json_store import snapshot_store

        monkeypatch.setattr(path_module, "SNAPSHOTS_DIR", tmp_path)
        monkeypatch.setattr(snapshot_store, "SNAPSHOTS_DIR", tmp_path)
        monkeypatch.setattr(snapshot_services, "SNAPSHOTS_DIR", tmp_path)

        original = Snapshot()
        original.add_snapshot_item("US_EQUITY", "S&P500", 100000)
        original.add_snapshot_item("KR_BOND", "Treasury", 50000)
        original.add_snapshot_item("US_EQUITY", "Nasdaq", 30000)

        save_snapshot(original)
        loaded = load_latest_snapshot()

        assert loaded.currency == original.currency
        assert len(loaded.items) == len(original.items)
        for orig_item, loaded_item in zip(original.items, loaded.items, strict=True):
            assert loaded_item.asset_id == orig_item.asset_id
            assert loaded_item.label == orig_item.label
            assert loaded_item.amount == orig_item.amount


class TestRemoveItemFromSnapshot:
    """Tests for remove_item_from_snapshot function."""

    def test_removes_item_and_returns_same_instance(self):
        """remove_item_from_snapshot should mutate and return the same snapshot."""
        snapshot = Snapshot()
        snapshot.add_snapshot_item("US_EQUITY", "S&P500", 100000)
        snapshot.add_snapshot_item("KR_BOND", "Treasury", 50000)

        result = remove_item_from_snapshot(snapshot, 0)

        assert result is snapshot
        assert len(snapshot.items) == 1
        assert snapshot.items[0].asset_id == "KR_BOND"

    def test_remove_out_of_range_raises_index_error(self):
        """remove_item_from_snapshot should propagate IndexError for invalid index."""
        snapshot = Snapshot()
        snapshot.add_snapshot_item("US_EQUITY", "S&P500", 100000)

        with pytest.raises(IndexError):
            remove_item_from_snapshot(snapshot, 5)


class TestReplaceItemInSnapshot:
    """Tests for replace_item_in_snapshot function."""

    def test_replaces_item_and_returns_same_instance(self):
        """replace_item_in_snapshot should mutate and return the same snapshot."""
        snapshot = Snapshot()
        snapshot.add_snapshot_item("US_EQUITY", "S&P500", 100000)

        result = replace_item_in_snapshot(snapshot, 0, "GOLD", "Gold ETF", 500000)

        assert result is snapshot
        assert len(snapshot.items) == 1
        assert snapshot.items[0].asset_id == "GOLD"
        assert snapshot.items[0].label == "Gold ETF"
        assert snapshot.items[0].amount == 500000

    def test_replace_out_of_range_raises_index_error(self):
        """replace_item_in_snapshot should propagate IndexError for invalid index."""
        snapshot = Snapshot()

        with pytest.raises(IndexError):
            replace_item_in_snapshot(snapshot, 0, "GOLD", "Gold", 500000)


class TestSaveSnapshotOverwrite:
    """Tests for save_snapshot_overwrite function."""

    def test_saves_to_specified_file(self, tmp_path, monkeypatch):
        """save_snapshot_overwrite should save to the exact file name given."""
        from portfotrack.storage.json_store import snapshot_store

        monkeypatch.setattr(snapshot_store, "SNAPSHOTS_DIR", tmp_path)

        snapshot = Snapshot(date="2026-02-12", currency="KRW")
        snapshot.add_snapshot_item("US_EQUITY", "S&P500", 100000)

        save_snapshot_overwrite(snapshot, "snapshot_2026-02-12_v1.json")

        file_path = tmp_path / "snapshot_2026-02-12_v1.json"
        assert file_path.exists()

        with open(file_path) as f:
            data = json.load(f)
        assert data["date"] == "2026-02-12"
        assert len(data["items"]) == 1

    def test_overwrites_existing_file(self, tmp_path, monkeypatch):
        """save_snapshot_overwrite should overwrite existing file content."""
        from portfotrack.storage.json_store import snapshot_store

        monkeypatch.setattr(snapshot_store, "SNAPSHOTS_DIR", tmp_path)

        file_name = "snapshot_2026-02-12_v1.json"

        # First save
        snapshot1 = Snapshot(date="2026-02-12")
        snapshot1.add_snapshot_item("US_EQUITY", "S&P500", 100000)
        save_snapshot_overwrite(snapshot1, file_name)

        # Second save (overwrite)
        snapshot2 = Snapshot(date="2026-02-12")
        snapshot2.add_snapshot_item("GOLD", "Gold ETF", 500000)
        save_snapshot_overwrite(snapshot2, file_name)

        with open(tmp_path / file_name) as f:
            data = json.load(f)
        assert len(data["items"]) == 1
        assert data["items"][0]["asset_id"] == "GOLD"

    def test_preserves_original_date(self, tmp_path, monkeypatch):
        """save_snapshot_overwrite should keep snapshot date unchanged."""
        from portfotrack.storage.json_store import snapshot_store

        monkeypatch.setattr(snapshot_store, "SNAPSHOTS_DIR", tmp_path)

        snapshot = Snapshot(date="2026-01-15")
        snapshot.add_snapshot_item("CASH", "KRW", 10000)

        save_snapshot_overwrite(snapshot, "snapshot_2026-01-15_v1.json")

        with open(tmp_path / "snapshot_2026-01-15_v1.json") as f:
            data = json.load(f)
        assert data["date"] == "2026-01-15"


class TestLoadSnapshotByFilename:
    """Tests for load_snapshot_by_filename function."""

    def test_loads_snapshot_by_filename(self, tmp_path, monkeypatch):
        """load_snapshot_by_filename should load the specified snapshot file."""
        from portfotrack.services import snapshot_services
        from portfotrack.storage.json_store import snapshot_store

        monkeypatch.setattr(snapshot_store, "SNAPSHOTS_DIR", tmp_path)
        monkeypatch.setattr(snapshot_services, "SNAPSHOTS_DIR", tmp_path)

        file_name = "snapshot_2026-02-14_v1.json"
        (tmp_path / file_name).write_text(
            json.dumps(
                {
                    "date": "2026-02-14",
                    "currency": "KRW",
                    "items": [
                        {"asset_id": "US_EQUITY", "label": "S&P500", "amount": 100000}
                    ],
                },
                ensure_ascii=False,
            )
        )

        snapshot = load_snapshot_by_filename(file_name)

        assert isinstance(snapshot, Snapshot)
        assert snapshot.date == "2026-02-14"
        assert len(snapshot.items) == 1
        assert snapshot.items[0].asset_id == "US_EQUITY"
        assert snapshot.items[0].amount == 100000

    def test_nonexistent_file_raises_error(self, tmp_path, monkeypatch):
        """load_snapshot_by_filename should raise SnapshotNotFoundError for missing file."""
        from portfotrack.storage.json_store import snapshot_store

        monkeypatch.setattr(snapshot_store, "SNAPSHOTS_DIR", tmp_path)

        with pytest.raises(SnapshotNotFoundError):
            load_snapshot_by_filename("snapshot_9999-12-31_v1.json")
