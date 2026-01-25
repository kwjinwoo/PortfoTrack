import pytest

from portfotrack.domain.asset import Asset
from portfotrack.domain.target import TargetAllocation, Tolerance


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

    with pytest.raises(ValueError, match="already in Target Portfolio."):
        target_allocation.add_asset(asset_other, 0.6, tol_ok)


@pytest.mark.parametrize("target_ratio", [-0.1, 1.01])
def test_add_asset_malform_target_ratio_raise_value_error(
    target_ratio: float, tol_ok: Tolerance
) -> None:
    target_allocation = TargetAllocation()
    asset_a = Asset("a", "Asset A", "growth")

    with pytest.raises(ValueError, match="target_ratio must be between 0 and 1"):
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

    with pytest.raises(ValueError):
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

    with pytest.raises(ValueError):
        target_allocation.validate_total()


def test_validate_total_upper_one_raise_value_error(tol_ok: Tolerance) -> None:
    target_allocation = TargetAllocation()

    asset_a = Asset("a", "Asset A", "growth")
    asset_b = Asset("b", "Asset B", "growth")

    target_allocation.add_asset(asset_a, 0.8, tol_ok)
    target_allocation.add_asset(asset_b, 0.21, tol_ok)

    with pytest.raises(ValueError):
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
