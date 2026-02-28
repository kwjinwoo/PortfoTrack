import pytest

from portfotrack.domain.optional_bet import OptionalBetSnapshot
from portfotrack.storage.serialization.optional_bet_json import (
    OptionalBetItemDTO,
    OptionalBetSnapshotDTO,
    dto_to_optional_bet,
    optional_bet_to_dto,
)


def make_item_dto(
    *,
    asset_id: str = "bitcoin",
    name: str = "Bitcoin",
    cap_ratio: float = 0.05,
    amount: int = 1_000_000,
) -> OptionalBetItemDTO:
    """Helper to create a valid OptionalBetItemDTO for tests."""
    return {
        "asset_id": asset_id,
        "name": name,
        "cap_ratio": cap_ratio,
        "amount": amount,
    }


# ---------------------------------------------------------------------------
# optional_bet_to_dto
# ---------------------------------------------------------------------------


def test_to_dto_empty() -> None:
    snapshot = OptionalBetSnapshot(date="2026-03-01", currency="KRW")
    dto = optional_bet_to_dto(snapshot)

    assert dto == {"date": "2026-03-01", "currency": "KRW", "items": []}


def test_to_dto_single_item() -> None:
    snapshot = OptionalBetSnapshot(date="2026-03-01")
    snapshot.add_item("bitcoin", "Bitcoin", 0.05, 1_000_000)

    dto = optional_bet_to_dto(snapshot)

    assert dto == {
        "date": "2026-03-01",
        "currency": "KRW",
        "items": [
            {
                "asset_id": "bitcoin",
                "name": "Bitcoin",
                "cap_ratio": 0.05,
                "amount": 1_000_000,
            },
        ],
    }


def test_to_dto_multiple_items_sorted_by_asset_id() -> None:
    snapshot = OptionalBetSnapshot(date="2026-03-01")
    snapshot.add_item("solana", "Solana", 0.03, 500_000)
    snapshot.add_item("bitcoin", "Bitcoin", 0.05, 1_000_000)

    dto = optional_bet_to_dto(snapshot)

    assert len(dto["items"]) == 2
    assert dto["items"][0]["asset_id"] == "bitcoin"
    assert dto["items"][1]["asset_id"] == "solana"


# ---------------------------------------------------------------------------
# dto_to_optional_bet
# ---------------------------------------------------------------------------


def test_from_dto_empty() -> None:
    dto: OptionalBetSnapshotDTO = {
        "date": "2026-03-01",
        "currency": "KRW",
        "items": [],
    }
    snapshot = dto_to_optional_bet(dto)

    assert snapshot.date == "2026-03-01"
    assert snapshot.currency == "KRW"
    assert snapshot.items == []


def test_from_dto_single_item() -> None:
    dto: OptionalBetSnapshotDTO = {
        "date": "2026-03-01",
        "currency": "KRW",
        "items": [make_item_dto()],
    }
    snapshot = dto_to_optional_bet(dto)

    assert len(snapshot.items) == 1
    assert snapshot.items[0].asset_id == "bitcoin"
    assert snapshot.items[0].name == "Bitcoin"
    assert snapshot.items[0].cap_ratio == pytest.approx(0.05)
    assert snapshot.items[0].amount == 1_000_000


def test_from_dto_multiple_items() -> None:
    dto: OptionalBetSnapshotDTO = {
        "date": "2026-03-01",
        "currency": "KRW",
        "items": [
            make_item_dto(asset_id="bitcoin", name="Bitcoin", cap_ratio=0.05),
            make_item_dto(
                asset_id="solana", name="Solana", cap_ratio=0.03, amount=500_000
            ),
        ],
    }
    snapshot = dto_to_optional_bet(dto)

    assert len(snapshot.items) == 2


# ---------------------------------------------------------------------------
# dto_to_optional_bet — invariant violations (programmer errors)
# ---------------------------------------------------------------------------


def test_from_dto_item_not_dict_raises_type_error() -> None:
    dto = {"date": "2026-03-01", "currency": "KRW", "items": ["not_a_dict"]}

    with pytest.raises(TypeError, match="item dto must be a dict"):
        dto_to_optional_bet(dto)  # type: ignore[arg-type]


def test_from_dto_item_missing_key_raises_runtime_error() -> None:
    dto = {
        "date": "2026-03-01",
        "currency": "KRW",
        "items": [{"asset_id": "bitcoin", "name": "Bitcoin"}],
    }

    with pytest.raises(RuntimeError, match="missing key 'cap_ratio'"):
        dto_to_optional_bet(dto)  # type: ignore[arg-type]


def test_from_dto_item_invalid_asset_id_type_raises() -> None:
    dto = {
        "date": "2026-03-01",
        "currency": "KRW",
        "items": [
            {"asset_id": 123, "name": "Bitcoin", "cap_ratio": 0.05, "amount": 1000}
        ],
    }

    with pytest.raises(TypeError, match="'asset_id' must be a non-empty string"):
        dto_to_optional_bet(dto)  # type: ignore[arg-type]


def test_from_dto_item_empty_asset_id_raises() -> None:
    dto = {
        "date": "2026-03-01",
        "currency": "KRW",
        "items": [
            {"asset_id": "", "name": "Bitcoin", "cap_ratio": 0.05, "amount": 1000}
        ],
    }

    with pytest.raises(TypeError, match="'asset_id' must be a non-empty string"):
        dto_to_optional_bet(dto)  # type: ignore[arg-type]


def test_from_dto_item_invalid_name_type_raises() -> None:
    dto = {
        "date": "2026-03-01",
        "currency": "KRW",
        "items": [
            {"asset_id": "bitcoin", "name": 123, "cap_ratio": 0.05, "amount": 1000}
        ],
    }

    with pytest.raises(TypeError, match="'name' must be a non-empty string"):
        dto_to_optional_bet(dto)  # type: ignore[arg-type]


def test_from_dto_item_invalid_cap_ratio_type_raises() -> None:
    dto = {
        "date": "2026-03-01",
        "currency": "KRW",
        "items": [
            {
                "asset_id": "bitcoin",
                "name": "Bitcoin",
                "cap_ratio": "bad",
                "amount": 1000,
            }
        ],
    }

    with pytest.raises(TypeError, match="'cap_ratio' must be a number"):
        dto_to_optional_bet(dto)  # type: ignore[arg-type]


def test_from_dto_item_bool_cap_ratio_raises() -> None:
    dto = {
        "date": "2026-03-01",
        "currency": "KRW",
        "items": [
            {
                "asset_id": "bitcoin",
                "name": "Bitcoin",
                "cap_ratio": True,
                "amount": 1000,
            }
        ],
    }

    with pytest.raises(TypeError, match="'cap_ratio' must be a number"):
        dto_to_optional_bet(dto)  # type: ignore[arg-type]


def test_from_dto_item_invalid_amount_type_raises() -> None:
    dto = {
        "date": "2026-03-01",
        "currency": "KRW",
        "items": [
            {
                "asset_id": "bitcoin",
                "name": "Bitcoin",
                "cap_ratio": 0.05,
                "amount": "bad",
            }
        ],
    }

    with pytest.raises(TypeError, match="'amount' must be an int"):
        dto_to_optional_bet(dto)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Round-trip
# ---------------------------------------------------------------------------


def test_roundtrip_domain_to_dto_to_domain() -> None:
    original = OptionalBetSnapshot(date="2026-03-01", currency="KRW")
    original.add_item("bitcoin", "Bitcoin", 0.05, 1_000_000)
    original.add_item("solana", "Solana", 0.03, 500_000)

    dto = optional_bet_to_dto(original)
    restored = dto_to_optional_bet(dto)

    assert restored.date == original.date
    assert restored.currency == original.currency
    assert len(restored.items) == len(original.items)

    # DTO sorts by asset_id, so restored order may differ
    original_by_id = {item.asset_id: item for item in original.items}
    for item in restored.items:
        orig = original_by_id[item.asset_id]
        assert item.name == orig.name
        assert item.cap_ratio == pytest.approx(orig.cap_ratio)
        assert item.amount == orig.amount


def test_roundtrip_dto_to_domain_to_dto() -> None:
    dto1: OptionalBetSnapshotDTO = {
        "date": "2026-03-01",
        "currency": "KRW",
        "items": [
            make_item_dto(asset_id="bitcoin", name="Bitcoin", cap_ratio=0.05),
            make_item_dto(
                asset_id="solana", name="Solana", cap_ratio=0.03, amount=500_000
            ),
        ],
    }

    snapshot = dto_to_optional_bet(dto1)
    dto2 = optional_bet_to_dto(snapshot)

    assert dto1 == dto2
