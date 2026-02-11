import pytest

from portfotrack.domain.snapshot import Snapshot
from portfotrack.storage.serialization.snapshot_json import (
    SnapshotDTO,
    SnapshotItemDTO,
    dto_to_snapshot,
    snapshot_to_dto,
)


def make_item_dto(
    *,
    asset_id: str = "us_equity",
    label: str = "S&P500",
    amount: int = 1_000_000,
) -> SnapshotItemDTO:
    """Helper to create a valid SnapshotItemDTO for tests."""
    return {"asset_id": asset_id, "label": label, "amount": amount}


# ---------------------------------------------------------------------------
# snapshot_to_dto
# ---------------------------------------------------------------------------


def test_snapshot_to_dto_empty() -> None:
    snapshot = Snapshot(date="2026-02-11", currency="KRW")
    dto = snapshot_to_dto(snapshot)

    assert dto == {"date": "2026-02-11", "currency": "KRW", "items": []}


def test_snapshot_to_dto_single_item() -> None:
    snapshot = Snapshot(date="2026-02-11", currency="KRW")
    snapshot.add_snapshot_item("us_equity", "S&P500", 5_000_000)

    dto = snapshot_to_dto(snapshot)

    assert dto == {
        "date": "2026-02-11",
        "currency": "KRW",
        "items": [
            {"asset_id": "us_equity", "label": "S&P500", "amount": 5_000_000},
        ],
    }


def test_snapshot_to_dto_multiple_items_preserves_order() -> None:
    snapshot = Snapshot(date="2026-02-11", currency="KRW")
    snapshot.add_snapshot_item("us_equity", "S&P500", 3_000_000)
    snapshot.add_snapshot_item("us_equity", "Nasdaq100", 2_000_000)
    snapshot.add_snapshot_item("kr_bond", "10-Year Government Bond", 5_000_000)

    dto = snapshot_to_dto(snapshot)

    assert len(dto["items"]) == 3
    assert dto["items"][0]["asset_id"] == "us_equity"
    assert dto["items"][0]["label"] == "S&P500"
    assert dto["items"][1]["label"] == "Nasdaq100"
    assert dto["items"][2]["asset_id"] == "kr_bond"


def test_snapshot_to_dto_includes_date_and_currency() -> None:
    snapshot = Snapshot(date="2025-12-25", currency="USD")
    dto = snapshot_to_dto(snapshot)

    assert dto["date"] == "2025-12-25"
    assert dto["currency"] == "USD"


# ---------------------------------------------------------------------------
# dto_to_snapshot
# ---------------------------------------------------------------------------


def test_dto_to_snapshot_empty() -> None:
    dto: SnapshotDTO = {"date": "2026-02-11", "currency": "KRW", "items": []}
    snapshot = dto_to_snapshot(dto)

    assert snapshot.date == "2026-02-11"
    assert snapshot.currency == "KRW"
    assert snapshot.items == []


def test_dto_to_snapshot_single_item() -> None:
    dto: SnapshotDTO = {
        "date": "2026-02-11",
        "currency": "KRW",
        "items": [
            make_item_dto(asset_id="us_equity", label="S&P500", amount=5_000_000)
        ],
    }
    snapshot = dto_to_snapshot(dto)

    assert len(snapshot.items) == 1
    assert snapshot.items[0].asset_id == "us_equity"
    assert snapshot.items[0].label == "S&P500"
    assert snapshot.items[0].amount == 5_000_000


def test_dto_to_snapshot_multiple_items_preserves_order() -> None:
    dto: SnapshotDTO = {
        "date": "2026-02-11",
        "currency": "KRW",
        "items": [
            make_item_dto(asset_id="us_equity", label="S&P500", amount=3_000_000),
            make_item_dto(asset_id="us_equity", label="Nasdaq100", amount=2_000_000),
            make_item_dto(
                asset_id="kr_bond", label="10-Year Government Bond", amount=5_000_000
            ),
        ],
    }
    snapshot = dto_to_snapshot(dto)

    assert len(snapshot.items) == 3
    assert snapshot.items[0].label == "S&P500"
    assert snapshot.items[1].label == "Nasdaq100"
    assert snapshot.items[2].label == "10-Year Government Bond"


# ---------------------------------------------------------------------------
# dto_to_snapshot — invariant violations (programmer errors)
# ---------------------------------------------------------------------------


def test_dto_to_snapshot_item_not_dict_raises_type_error() -> None:
    dto = {"date": "2026-02-11", "currency": "KRW", "items": ["not_a_dict"]}

    with pytest.raises(TypeError, match="item dto must be a dict"):
        dto_to_snapshot(dto)  # type: ignore[arg-type]


def test_dto_to_snapshot_item_missing_key_raises_runtime_error() -> None:
    dto = {
        "date": "2026-02-11",
        "currency": "KRW",
        "items": [{"asset_id": "a", "label": "A"}],  # missing 'amount'
    }

    with pytest.raises(RuntimeError, match="missing key 'amount'"):
        dto_to_snapshot(dto)  # type: ignore[arg-type]


def test_dto_to_snapshot_item_invalid_asset_id_type_raises() -> None:
    dto = {
        "date": "2026-02-11",
        "currency": "KRW",
        "items": [{"asset_id": 123, "label": "A", "amount": 1000}],
    }

    with pytest.raises(TypeError, match="'asset_id' must be a non-empty string"):
        dto_to_snapshot(dto)  # type: ignore[arg-type]


def test_dto_to_snapshot_item_invalid_amount_type_raises() -> None:
    dto = {
        "date": "2026-02-11",
        "currency": "KRW",
        "items": [{"asset_id": "a", "label": "A", "amount": "not_int"}],
    }

    with pytest.raises(TypeError, match="'amount' must be an int"):
        dto_to_snapshot(dto)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Round-trip
# ---------------------------------------------------------------------------


def test_roundtrip_snapshot_to_dto_to_snapshot() -> None:
    original = Snapshot(date="2026-02-11", currency="KRW")
    original.add_snapshot_item("us_equity", "S&P500", 3_000_000)
    original.add_snapshot_item("kr_bond", "10-Year Government Bond", 5_000_000)

    dto = snapshot_to_dto(original)
    restored = dto_to_snapshot(dto)

    assert restored.date == original.date
    assert restored.currency == original.currency
    assert len(restored.items) == len(original.items)
    for orig_item, rest_item in zip(original.items, restored.items, strict=True):
        assert rest_item.asset_id == orig_item.asset_id
        assert rest_item.label == orig_item.label
        assert rest_item.amount == orig_item.amount


def test_roundtrip_dto_to_snapshot_to_dto() -> None:
    dto1: SnapshotDTO = {
        "date": "2026-01-15",
        "currency": "KRW",
        "items": [
            make_item_dto(asset_id="gold", label="Gold ETF", amount=2_000_000),
            make_item_dto(asset_id="cash", label="KRW Cash", amount=10_000_000),
        ],
    }

    snapshot = dto_to_snapshot(dto1)
    dto2 = snapshot_to_dto(snapshot)

    assert dto2 == dto1
