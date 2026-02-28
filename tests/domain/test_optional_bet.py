import pytest

from portfotrack.domain.optional_bet import (
    CapBreachResult,
    OptionalBetItem,
    OptionalBetSnapshot,
)
from portfotrack.domain.optional_bet.error_codes import OptionalBetErrorCode
from portfotrack.domain.optional_bet.errors import (
    DuplicateOptionalBetError,
    InvalidCapRatioError,
    OptionalBetAssetNotFoundError,
)
from portfotrack.domain.optional_bet.optional_bet import check_cap_breaches

# ---------------------------
# OptionalBetItem
# ---------------------------


class TestOptionalBetItem:
    """Tests for OptionalBetItem dataclass."""

    def test_create_item(self) -> None:
        item = OptionalBetItem(
            asset_id="bitcoin", name="Bitcoin", cap_ratio=0.05, amount=1_000_000
        )

        assert item.asset_id == "bitcoin"
        assert item.name == "Bitcoin"
        assert item.cap_ratio == pytest.approx(0.05)
        assert item.amount == 1_000_000

    def test_item_is_frozen(self) -> None:
        item = OptionalBetItem(
            asset_id="bitcoin", name="Bitcoin", cap_ratio=0.05, amount=1_000_000
        )

        with pytest.raises(AttributeError):
            item.amount = 2_000_000  # type: ignore[misc]

    def test_item_equality_by_value(self) -> None:
        item_a = OptionalBetItem(
            asset_id="bitcoin", name="Bitcoin", cap_ratio=0.05, amount=1_000_000
        )
        item_b = OptionalBetItem(
            asset_id="bitcoin", name="Bitcoin", cap_ratio=0.05, amount=1_000_000
        )

        assert item_a == item_b

    def test_items_with_different_amount_are_not_equal(self) -> None:
        item_a = OptionalBetItem(
            asset_id="bitcoin", name="Bitcoin", cap_ratio=0.05, amount=1_000_000
        )
        item_b = OptionalBetItem(
            asset_id="bitcoin", name="Bitcoin", cap_ratio=0.05, amount=2_000_000
        )

        assert item_a != item_b


# ---------------------------
# OptionalBetSnapshot — init
# ---------------------------


class TestOptionalBetSnapshotInit:
    """Tests for OptionalBetSnapshot initialization."""

    def test_init_empty_snapshot(self) -> None:
        snapshot = OptionalBetSnapshot()

        assert snapshot.date is not None
        assert snapshot.currency == "KRW"
        assert snapshot.items == []

    def test_init_with_explicit_date(self) -> None:
        snapshot = OptionalBetSnapshot(date="2026-03-01")

        assert snapshot.date == "2026-03-01"


# ---------------------------
# OptionalBetSnapshot — add_item
# ---------------------------


class TestAddItem:
    """Tests for OptionalBetSnapshot.add_item method."""

    def test_add_item_correctly(self) -> None:
        snapshot = OptionalBetSnapshot(date="2026-03-01")

        snapshot.add_item("bitcoin", "Bitcoin", 0.05, 1_000_000)

        assert len(snapshot.items) == 1
        assert snapshot.items[0].asset_id == "bitcoin"
        assert snapshot.items[0].name == "Bitcoin"
        assert snapshot.items[0].cap_ratio == pytest.approx(0.05)
        assert snapshot.items[0].amount == 1_000_000

    def test_add_multiple_items(self) -> None:
        snapshot = OptionalBetSnapshot(date="2026-03-01")

        snapshot.add_item("bitcoin", "Bitcoin", 0.05, 1_000_000)
        snapshot.add_item("solana", "Solana", 0.03, 500_000)

        assert len(snapshot.items) == 2

    def test_add_duplicate_asset_id_raises_error(self) -> None:
        snapshot = OptionalBetSnapshot(date="2026-03-01")
        snapshot.add_item("bitcoin", "Bitcoin", 0.05, 1_000_000)

        with pytest.raises(
            DuplicateOptionalBetError,
            match=OptionalBetErrorCode.OPTIONAL_BET_DUPLICATE_ASSET,
        ):
            snapshot.add_item("bitcoin", "Bitcoin BTC", 0.03, 2_000_000)

    @pytest.mark.parametrize("bad_ratio", [0.0, 1.0, -0.1, 1.5])
    def test_add_item_invalid_cap_ratio_raises_error(self, bad_ratio: float) -> None:
        snapshot = OptionalBetSnapshot(date="2026-03-01")

        with pytest.raises(
            InvalidCapRatioError,
            match=OptionalBetErrorCode.OPTIONAL_BET_INVALID_CAP_RATIO,
        ):
            snapshot.add_item("bitcoin", "Bitcoin", bad_ratio, 1_000_000)

    @pytest.mark.parametrize("good_ratio", [0.01, 0.5, 0.99])
    def test_add_item_valid_cap_ratio_boundary(self, good_ratio: float) -> None:
        snapshot = OptionalBetSnapshot(date="2026-03-01")

        snapshot.add_item("bitcoin", "Bitcoin", good_ratio, 1_000_000)

        assert snapshot.items[0].cap_ratio == pytest.approx(good_ratio)

    def test_add_item_zero_amount_allowed(self) -> None:
        snapshot = OptionalBetSnapshot(date="2026-03-01")

        snapshot.add_item("bitcoin", "Bitcoin", 0.05, 0)

        assert snapshot.items[0].amount == 0

    def test_add_item_negative_amount_raises_value_error(self) -> None:
        snapshot = OptionalBetSnapshot(date="2026-03-01")

        with pytest.raises(ValueError):
            snapshot.add_item("bitcoin", "Bitcoin", 0.05, -100)


# ---------------------------
# OptionalBetSnapshot — remove_item
# ---------------------------


class TestRemoveItem:
    """Tests for OptionalBetSnapshot.remove_item method."""

    def test_remove_existing_item(self) -> None:
        snapshot = OptionalBetSnapshot(date="2026-03-01")
        snapshot.add_item("bitcoin", "Bitcoin", 0.05, 1_000_000)
        snapshot.add_item("solana", "Solana", 0.03, 500_000)

        snapshot.remove_item("bitcoin")

        assert len(snapshot.items) == 1
        assert snapshot.items[0].asset_id == "solana"

    def test_remove_only_item_leaves_empty(self) -> None:
        snapshot = OptionalBetSnapshot(date="2026-03-01")
        snapshot.add_item("bitcoin", "Bitcoin", 0.05, 1_000_000)

        snapshot.remove_item("bitcoin")

        assert len(snapshot.items) == 0

    def test_remove_nonexistent_item_raises_error(self) -> None:
        snapshot = OptionalBetSnapshot(date="2026-03-01")
        snapshot.add_item("bitcoin", "Bitcoin", 0.05, 1_000_000)

        with pytest.raises(
            OptionalBetAssetNotFoundError,
            match=OptionalBetErrorCode.OPTIONAL_BET_ASSET_NOT_FOUND,
        ):
            snapshot.remove_item("ethereum")

    def test_remove_from_empty_snapshot_raises_error(self) -> None:
        snapshot = OptionalBetSnapshot(date="2026-03-01")

        with pytest.raises(
            OptionalBetAssetNotFoundError,
            match=OptionalBetErrorCode.OPTIONAL_BET_ASSET_NOT_FOUND,
        ):
            snapshot.remove_item("bitcoin")


# ---------------------------
# OptionalBetSnapshot — update_item
# ---------------------------


class TestUpdateItem:
    """Tests for OptionalBetSnapshot.update_item method."""

    def test_update_all_fields(self) -> None:
        snapshot = OptionalBetSnapshot(date="2026-03-01")
        snapshot.add_item("bitcoin", "Bitcoin", 0.05, 1_000_000)

        snapshot.update_item(
            "bitcoin", name="Bitcoin BTC", cap_ratio=0.08, amount=2_000_000
        )

        assert snapshot.items[0].name == "Bitcoin BTC"
        assert snapshot.items[0].cap_ratio == pytest.approx(0.08)
        assert snapshot.items[0].amount == 2_000_000

    def test_update_name_only(self) -> None:
        snapshot = OptionalBetSnapshot(date="2026-03-01")
        snapshot.add_item("bitcoin", "Bitcoin", 0.05, 1_000_000)

        snapshot.update_item("bitcoin", name="BTC")

        assert snapshot.items[0].name == "BTC"
        assert snapshot.items[0].cap_ratio == pytest.approx(0.05)
        assert snapshot.items[0].amount == 1_000_000

    def test_update_cap_ratio_only(self) -> None:
        snapshot = OptionalBetSnapshot(date="2026-03-01")
        snapshot.add_item("bitcoin", "Bitcoin", 0.05, 1_000_000)

        snapshot.update_item("bitcoin", cap_ratio=0.10)

        assert snapshot.items[0].name == "Bitcoin"
        assert snapshot.items[0].cap_ratio == pytest.approx(0.10)
        assert snapshot.items[0].amount == 1_000_000

    def test_update_amount_only(self) -> None:
        snapshot = OptionalBetSnapshot(date="2026-03-01")
        snapshot.add_item("bitcoin", "Bitcoin", 0.05, 1_000_000)

        snapshot.update_item("bitcoin", amount=3_000_000)

        assert snapshot.items[0].name == "Bitcoin"
        assert snapshot.items[0].cap_ratio == pytest.approx(0.05)
        assert snapshot.items[0].amount == 3_000_000

    def test_update_nonexistent_item_raises_error(self) -> None:
        snapshot = OptionalBetSnapshot(date="2026-03-01")
        snapshot.add_item("bitcoin", "Bitcoin", 0.05, 1_000_000)

        with pytest.raises(
            OptionalBetAssetNotFoundError,
            match=OptionalBetErrorCode.OPTIONAL_BET_ASSET_NOT_FOUND,
        ):
            snapshot.update_item("ethereum", name="Eth")

    @pytest.mark.parametrize("bad_ratio", [0.0, 1.0, -0.1, 1.5])
    def test_update_invalid_cap_ratio_raises_error(self, bad_ratio: float) -> None:
        snapshot = OptionalBetSnapshot(date="2026-03-01")
        snapshot.add_item("bitcoin", "Bitcoin", 0.05, 1_000_000)

        with pytest.raises(
            InvalidCapRatioError,
            match=OptionalBetErrorCode.OPTIONAL_BET_INVALID_CAP_RATIO,
        ):
            snapshot.update_item("bitcoin", cap_ratio=bad_ratio)

    def test_update_negative_amount_raises_value_error(self) -> None:
        snapshot = OptionalBetSnapshot(date="2026-03-01")
        snapshot.add_item("bitcoin", "Bitcoin", 0.05, 1_000_000)

        with pytest.raises(ValueError):
            snapshot.update_item("bitcoin", amount=-100)

    def test_update_does_not_modify_on_validation_failure(self) -> None:
        snapshot = OptionalBetSnapshot(date="2026-03-01")
        snapshot.add_item("bitcoin", "Bitcoin", 0.05, 1_000_000)

        with pytest.raises(InvalidCapRatioError):
            snapshot.update_item("bitcoin", cap_ratio=0.0)

        assert snapshot.items[0].cap_ratio == pytest.approx(0.05)

    def test_update_preserves_other_items(self) -> None:
        snapshot = OptionalBetSnapshot(date="2026-03-01")
        snapshot.add_item("bitcoin", "Bitcoin", 0.05, 1_000_000)
        snapshot.add_item("solana", "Solana", 0.03, 500_000)

        snapshot.update_item("bitcoin", amount=2_000_000)

        assert snapshot.items[1].asset_id == "solana"
        assert snapshot.items[1].amount == 500_000


# ---------------------------
# OptionalBetSnapshot — total_amount
# ---------------------------


class TestTotalAmount:
    """Tests for OptionalBetSnapshot.total_amount method."""

    def test_total_amount_empty(self) -> None:
        snapshot = OptionalBetSnapshot(date="2026-03-01")

        assert snapshot.total_amount() == 0

    def test_total_amount_single_item(self) -> None:
        snapshot = OptionalBetSnapshot(date="2026-03-01")
        snapshot.add_item("bitcoin", "Bitcoin", 0.05, 1_000_000)

        assert snapshot.total_amount() == 1_000_000

    def test_total_amount_multiple_items(self) -> None:
        snapshot = OptionalBetSnapshot(date="2026-03-01")
        snapshot.add_item("bitcoin", "Bitcoin", 0.05, 1_000_000)
        snapshot.add_item("solana", "Solana", 0.03, 500_000)

        assert snapshot.total_amount() == 1_500_000


# ---------------------------
# check_cap_breaches
# ---------------------------


class TestCheckCapBreaches:
    """Tests for check_cap_breaches pure function."""

    def test_no_breach_when_under_cap(self) -> None:
        items = [
            OptionalBetItem("bitcoin", "Bitcoin", 0.05, 1_000_000),
        ]

        result = check_cap_breaches(items, main_portfolio_total=100_000_000)

        assert result == []

    def test_breach_when_over_cap(self) -> None:
        items = [
            OptionalBetItem("bitcoin", "Bitcoin", 0.05, 10_000_000),
        ]
        # total = 100_000_000 + 10_000_000 = 110_000_000
        # actual_ratio = 10_000_000 / 110_000_000 ≈ 0.0909
        result = check_cap_breaches(items, main_portfolio_total=100_000_000)

        assert len(result) == 1
        assert result[0].asset_id == "bitcoin"
        assert result[0].actual_ratio == pytest.approx(10_000_000 / 110_000_000)
        assert result[0].cap_ratio == pytest.approx(0.05)

    def test_no_breach_at_exact_cap(self) -> None:
        # total = 95 + 5 = 100, ratio = 5/100 = 0.05 == cap
        items = [
            OptionalBetItem("bitcoin", "Bitcoin", 0.05, 5),
        ]

        result = check_cap_breaches(items, main_portfolio_total=95)

        assert result == []

    def test_multiple_items_mixed_breaches(self) -> None:
        items = [
            OptionalBetItem("bitcoin", "Bitcoin", 0.05, 10_000_000),
            OptionalBetItem("solana", "Solana", 0.10, 2_000_000),
        ]
        # total = 100_000_000 + 10_000_000 + 2_000_000 = 112_000_000
        # bitcoin: 10_000_000/112_000_000 ≈ 0.0893 > 0.05 → breach
        # solana: 2_000_000/112_000_000 ≈ 0.0179 < 0.10 → ok
        result = check_cap_breaches(items, main_portfolio_total=100_000_000)

        assert len(result) == 1
        assert result[0].asset_id == "bitcoin"

    def test_empty_items_returns_empty(self) -> None:
        result = check_cap_breaches([], main_portfolio_total=100_000_000)

        assert result == []

    def test_zero_main_portfolio_total_returns_empty(self) -> None:
        items = [
            OptionalBetItem("bitcoin", "Bitcoin", 0.05, 1_000_000),
        ]
        # When main_portfolio_total=0, total = 0 + 1_000_000 = 1_000_000
        # ratio = 1_000_000 / 1_000_000 = 1.0 > 0.05 → breach
        result = check_cap_breaches(items, main_portfolio_total=0)

        assert len(result) == 1
        assert result[0].actual_ratio == pytest.approx(1.0)

    def test_all_amounts_zero_returns_empty(self) -> None:
        items = [
            OptionalBetItem("bitcoin", "Bitcoin", 0.05, 0),
        ]

        result = check_cap_breaches(items, main_portfolio_total=0)

        assert result == []

    def test_cap_breach_result_fields(self) -> None:
        breach = CapBreachResult(
            asset_id="bitcoin",
            name="Bitcoin",
            actual_ratio=0.08,
            cap_ratio=0.05,
        )

        assert breach.asset_id == "bitcoin"
        assert breach.name == "Bitcoin"
        assert breach.actual_ratio == pytest.approx(0.08)
        assert breach.cap_ratio == pytest.approx(0.05)
