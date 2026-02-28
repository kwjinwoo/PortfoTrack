import pytest

from portfotrack.domain.asset import Asset
from portfotrack.domain.target_allocation import TargetAllocation, Tolerance
from portfotrack.domain.target_allocation.error_codes import TargetErrorCode
from portfotrack.domain.target_allocation.errors import (
    AssetNotFoundError,
    DuplicateAssetError,
    InvalidTargetRatioError,
    InvalidToleranceBoundsError,
    TotalRatioMismatchError,
)


@pytest.fixture
def tol_ok() -> Tolerance:
    return {"lower": 0.25, "upper": 0.35}


@pytest.fixture
def tol_equal() -> Tolerance:
    return {"lower": 0.30, "upper": 0.30}


@pytest.fixture
def tol_bad_order() -> Tolerance:
    return {"lower": 0.4, "upper": 0.3}


@pytest.fixture
def tol_bad_lower() -> Tolerance:
    return {"lower": -0.1, "upper": 0.2}


@pytest.fixture
def tol_bad_upper() -> Tolerance:
    return {"lower": 0.2, "upper": 1.1}


def test_target_allocation_init_with_empty_targets() -> None:
    target_allocation = TargetAllocation()

    assert len(target_allocation.target_assets) == 0


def test_target_allocation_init_with_targets(tol_ok: Tolerance) -> None:
    asset = Asset("a1", "a1", "test")
    targets = {asset: (0.30, tol_ok)}

    target_allocation = TargetAllocation(target_assets=targets)

    assert len(target_allocation.target_assets) == 1
    assert target_allocation.target_assets[asset][0] == pytest.approx(0.30)
    assert target_allocation.target_assets[asset][1] == tol_ok

    targets.clear()
    assert len(target_allocation.target_assets) == 1


def test_add_asset_correctly(tol_ok: Tolerance) -> None:
    target_allocation = TargetAllocation()

    asset_a = Asset("a", "Asset A", "growth")
    target_allocation.add_asset(asset_a, 0.30, tol_ok)

    assert len(target_allocation.target_assets) == 1
    assert target_allocation.target_assets[asset_a] == (0.30, tol_ok)


@pytest.mark.parametrize(
    "asset_one, asset_other",
    [
        (Asset("a", "Asset A", "growth"), Asset("a", "Asset A", "growth")),
        (Asset("a", "Asset A", "growth"), Asset("a", "Asset A2", "other")),
    ],
)
def test_add_asset_duplicated_asset_rasise_value_error(
    asset_one: Asset, asset_other: Asset, tol_ok: Tolerance
) -> None:
    target_allocation = TargetAllocation()
    target_allocation.add_asset(asset_one, 0.30, tol_ok)

    with pytest.raises(
        DuplicateAssetError, match=TargetErrorCode.TARGET_DUPLICATE_ASSET
    ):
        target_allocation.add_asset(asset_other, 0.6, tol_ok)


@pytest.mark.parametrize("target_ratio", [-0.1, 1.01])
def test_add_asset_malform_target_ratio_raise_value_error(
    target_ratio: float, tol_ok: Tolerance
) -> None:
    target_allocation = TargetAllocation()
    asset_a = Asset("a", "Asset A", "growth")

    with pytest.raises(
        InvalidTargetRatioError, match=TargetErrorCode.TARGET_INVALID_RATIO
    ):
        target_allocation.add_asset(asset_a, target_ratio, tol_ok)


@pytest.mark.parametrize("target_ratio", [0.0, 1.0])
def test_add_asset_boundary_target_ratio_correltly(
    target_ratio: float, tol_ok: Tolerance
) -> None:
    target_allocation = TargetAllocation()
    asset_a = Asset("a", "Asset A", "growth")

    # no rasises
    target_allocation.add_asset(asset_a, target_ratio, tol_ok)


@pytest.mark.parametrize(
    "tolerance", ["tol_bad_order", "tol_bad_lower", "tol_bad_upper"]
)
def test_add_asset_bad_tolerance(request, tolerance: str) -> None:
    target_allocation = TargetAllocation()

    tol: Tolerance = request.getfixturevalue(tolerance)
    asset_a = Asset("a", "Asset A", "growth")

    with pytest.raises(
        InvalidToleranceBoundsError,
        match=TargetErrorCode.TARGET_INVALID_TOLERANCE_BOUNDS,
    ):
        target_allocation.add_asset(asset_a, 0.30, tol)


def test_add_asset_equal_tolerance(tol_equal: Tolerance) -> None:
    target_allocation = TargetAllocation()
    asset_a = Asset("a", "Asset A", "growth")

    # no raises
    target_allocation.add_asset(asset_a, 0.30, tol_equal)


def test_total_ratio_empty_target() -> None:
    target_allocation = TargetAllocation()

    assert target_allocation.total_ratio() == 0


def test_total_ratio_single_asset(tol_ok: Tolerance) -> None:
    target_allocation = TargetAllocation()

    asset_a = Asset("a", "Asset A", "growth")

    target_allocation.add_asset(asset_a, 0.3, tol_ok)

    assert target_allocation.total_ratio() == pytest.approx(0.3)


def test_total_ratio_multiple_assets(tol_ok: Tolerance) -> None:
    target_allocation = TargetAllocation()

    asset_a = Asset("a", "Asset A", "growth")
    asset_b = Asset("b", "Asset B", "growth")
    asset_c = Asset("c", "Asset C", "growth")

    target_allocation.add_asset(asset_a, 0.1, tol_ok)
    target_allocation.add_asset(asset_b, 0.2, tol_ok)
    target_allocation.add_asset(asset_c, 0.7, tol_ok)

    assert target_allocation.total_ratio() == pytest.approx(1.0)


def test_validate_total_under_one_raise_value_error(tol_ok: Tolerance) -> None:
    target_allocation = TargetAllocation()

    asset_a = Asset("a", "Asset A", "growth")
    asset_b = Asset("b", "Asset B", "growth")

    target_allocation.add_asset(asset_a, 0.1, tol_ok)
    target_allocation.add_asset(asset_b, 0.2, tol_ok)

    with pytest.raises(
        TotalRatioMismatchError, match=TargetErrorCode.TARGET_TOTAL_MISMATCH
    ):
        target_allocation.validate_total()


def test_validate_total_upper_one_raise_value_error(tol_ok: Tolerance) -> None:
    target_allocation = TargetAllocation()

    asset_a = Asset("a", "Asset A", "growth")
    asset_b = Asset("b", "Asset B", "growth")

    target_allocation.add_asset(asset_a, 0.8, tol_ok)
    target_allocation.add_asset(asset_b, 0.21, tol_ok)

    with pytest.raises(
        TotalRatioMismatchError, match=TargetErrorCode.TARGET_TOTAL_MISMATCH
    ):
        target_allocation.validate_total()


def test_validate_total_boundary(tol_ok: Tolerance) -> None:
    target_allocation = TargetAllocation()

    asset_a = Asset("a", "Asset A", "growth")
    asset_b = Asset("b", "Asset B", "growth")
    asset_c = Asset("c", "Asset C", "growth")

    target_allocation.add_asset(asset_a, 0.1, tol_ok)
    target_allocation.add_asset(asset_b, 0.2, tol_ok)
    target_allocation.add_asset(asset_c, 0.7, tol_ok)

    # no raises
    target_allocation.validate_total()


# ---------------------------
# get_asset_ids
# ---------------------------


def test_get_asset_ids_empty_target() -> None:
    target_allocation = TargetAllocation()

    assert target_allocation.get_asset_ids() == []


def test_get_asset_ids_single_asset(tol_ok: Tolerance) -> None:
    target_allocation = TargetAllocation()
    target_allocation.add_asset(Asset("us_equity", "US Equity", "growth"), 0.5, tol_ok)

    result = target_allocation.get_asset_ids()

    assert result == ["us_equity"]


def test_get_asset_ids_multiple_assets(tol_ok: Tolerance) -> None:
    target_allocation = TargetAllocation()
    target_allocation.add_asset(Asset("us_equity", "US Equity", "growth"), 0.3, tol_ok)
    target_allocation.add_asset(Asset("kr_bond", "KR Bond", "stability"), 0.3, tol_ok)
    target_allocation.add_asset(Asset("gold", "Gold", "hedge"), 0.4, tol_ok)

    result = target_allocation.get_asset_ids()

    assert len(result) == 3
    assert "us_equity" in result
    assert "kr_bond" in result
    assert "gold" in result


# ---------------------------
# is_valid_asset_id
# ---------------------------


def test_is_valid_asset_id_returns_true_for_existing(tol_ok: Tolerance) -> None:
    target_allocation = TargetAllocation()
    target_allocation.add_asset(Asset("us_equity", "US Equity", "growth"), 0.5, tol_ok)

    assert target_allocation.is_valid_asset_id("us_equity") is True


def test_is_valid_asset_id_returns_false_for_missing(tol_ok: Tolerance) -> None:
    target_allocation = TargetAllocation()
    target_allocation.add_asset(Asset("us_equity", "US Equity", "growth"), 0.5, tol_ok)

    assert target_allocation.is_valid_asset_id("kr_bond") is False


def test_is_valid_asset_id_returns_false_for_empty_target() -> None:
    target_allocation = TargetAllocation()

    assert target_allocation.is_valid_asset_id("us_equity") is False


# ---------------------------
# remove_asset
# ---------------------------


class TestRemoveAsset:
    """Tests for TargetAllocation.remove_asset method."""

    def test_remove_existing_asset(self, tol_ok: Tolerance) -> None:
        target = TargetAllocation()
        asset_a = Asset("a", "Asset A", "growth")
        asset_b = Asset("b", "Asset B", "stability")
        target.add_asset(asset_a, 0.4, tol_ok)
        target.add_asset(asset_b, 0.6, tol_ok)

        target.remove_asset("a")

        assert len(target.target_assets) == 1
        assert not target.is_valid_asset_id("a")
        assert target.is_valid_asset_id("b")

    def test_remove_only_asset_leaves_empty(self, tol_ok: Tolerance) -> None:
        target = TargetAllocation()
        asset_a = Asset("a", "Asset A", "growth")
        target.add_asset(asset_a, 0.5, tol_ok)

        target.remove_asset("a")

        assert len(target.target_assets) == 0

    def test_remove_nonexistent_asset_raises_error(self, tol_ok: Tolerance) -> None:
        target = TargetAllocation()
        asset_a = Asset("a", "Asset A", "growth")
        target.add_asset(asset_a, 0.5, tol_ok)

        with pytest.raises(
            AssetNotFoundError, match=TargetErrorCode.TARGET_ASSET_NOT_FOUND
        ):
            target.remove_asset("nonexistent")

    def test_remove_from_empty_allocation_raises_error(self) -> None:
        target = TargetAllocation()

        with pytest.raises(
            AssetNotFoundError, match=TargetErrorCode.TARGET_ASSET_NOT_FOUND
        ):
            target.remove_asset("a")


# ---------------------------
# update_asset
# ---------------------------


class TestUpdateAsset:
    """Tests for TargetAllocation.update_asset method."""

    def test_update_ratio_and_tolerance(self, tol_ok: Tolerance) -> None:
        target = TargetAllocation()
        asset_a = Asset("a", "Asset A", "growth")
        target.add_asset(asset_a, 0.3, tol_ok)

        new_tol: Tolerance = {"lower": 0.10, "upper": 0.50}
        target.update_asset("a", 0.5, new_tol)

        assert target.target_assets[asset_a][0] == pytest.approx(0.5)
        assert target.target_assets[asset_a][1] == new_tol

    def test_update_preserves_other_assets(self, tol_ok: Tolerance) -> None:
        target = TargetAllocation()
        asset_a = Asset("a", "Asset A", "growth")
        asset_b = Asset("b", "Asset B", "stability")
        target.add_asset(asset_a, 0.3, tol_ok)
        target.add_asset(asset_b, 0.7, tol_ok)

        new_tol: Tolerance = {"lower": 0.10, "upper": 0.50}
        target.update_asset("a", 0.4, new_tol)

        assert target.target_assets[asset_a] == (0.4, new_tol)
        assert target.target_assets[asset_b] == (0.7, tol_ok)

    def test_update_nonexistent_asset_raises_error(self, tol_ok: Tolerance) -> None:
        target = TargetAllocation()
        asset_a = Asset("a", "Asset A", "growth")
        target.add_asset(asset_a, 0.3, tol_ok)

        with pytest.raises(
            AssetNotFoundError, match=TargetErrorCode.TARGET_ASSET_NOT_FOUND
        ):
            target.update_asset("nonexistent", 0.5, tol_ok)

    def test_update_empty_allocation_raises_error(self, tol_ok: Tolerance) -> None:
        target = TargetAllocation()

        with pytest.raises(
            AssetNotFoundError, match=TargetErrorCode.TARGET_ASSET_NOT_FOUND
        ):
            target.update_asset("a", 0.5, tol_ok)

    @pytest.mark.parametrize("bad_ratio", [-0.1, 1.01])
    def test_update_invalid_ratio_raises_error(
        self, bad_ratio: float, tol_ok: Tolerance
    ) -> None:
        target = TargetAllocation()
        asset_a = Asset("a", "Asset A", "growth")
        target.add_asset(asset_a, 0.3, tol_ok)

        with pytest.raises(
            InvalidTargetRatioError, match=TargetErrorCode.TARGET_INVALID_RATIO
        ):
            target.update_asset("a", bad_ratio, tol_ok)

    @pytest.mark.parametrize(
        "bad_tol",
        [
            {"lower": 0.4, "upper": 0.3},
            {"lower": -0.1, "upper": 0.2},
            {"lower": 0.2, "upper": 1.1},
        ],
    )
    def test_update_invalid_tolerance_raises_error(
        self, bad_tol: Tolerance, tol_ok: Tolerance
    ) -> None:
        target = TargetAllocation()
        asset_a = Asset("a", "Asset A", "growth")
        target.add_asset(asset_a, 0.3, tol_ok)

        with pytest.raises(
            InvalidToleranceBoundsError,
            match=TargetErrorCode.TARGET_INVALID_TOLERANCE_BOUNDS,
        ):
            target.update_asset("a", 0.3, bad_tol)

    def test_update_does_not_modify_on_validation_failure(
        self, tol_ok: Tolerance
    ) -> None:
        target = TargetAllocation()
        asset_a = Asset("a", "Asset A", "growth")
        target.add_asset(asset_a, 0.3, tol_ok)

        with pytest.raises(InvalidTargetRatioError):
            target.update_asset("a", -0.5, tol_ok)

        assert target.target_assets[asset_a] == (0.3, tol_ok)
