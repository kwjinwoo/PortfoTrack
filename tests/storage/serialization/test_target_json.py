# tests/infra/test_target_allocation_dto.py
from __future__ import annotations

import pytest

from portfotrack.domain.asset import Asset
from portfotrack.domain.target_allocation import TargetAllocation
from portfotrack.domain.target_allocation.errors import (
    DuplicateAssetError,
    InvalidTargetRatioError,
    InvalidToleranceBoundsError,
)
from portfotrack.storage.serialization.target_json import (
    AssetDTO,
    TargetAllocationDTO,
    dto_to_target,
    target_to_dto,
)


def make_asset_dto(
    *,
    asset_id: str,
    name: str | None = None,
    purpose: str = "growth",
    target_ratio: float = 0.5,
    lower: float = 0.0,
    upper: float = 1.0,
) -> AssetDTO:
    return {
        "id": asset_id,
        "name": name or f"Asset {asset_id}",
        "purpose": purpose,
        "target_ratio": target_ratio,
        "tolerance": {"lower": lower, "upper": upper},
    }


def normalize_target(
    target: TargetAllocation,
) -> dict[str, tuple[float, dict[str, float]]]:
    """Compare TargetAllocation by value (id-keyed), not by Asset object identity."""
    out: dict[str, tuple[float, dict[str, float]]] = {}
    for asset, (ratio, tol) in target.target_assets.items():
        out[asset.id] = (ratio, {"lower": tol["lower"], "upper": tol["upper"]})
    return out


def norm_dto_assets(dto: TargetAllocationDTO) -> dict[str, AssetDTO]:
    """Normalize dto['assets'] list into id-keyed mapping (order-insensitive compare)."""
    return {a["id"]: a for a in dto["assets"]}


# ---------------------------------------------------------------------------
# target_to_dto
# ---------------------------------------------------------------------------


def test_target_to_dto_empty() -> None:
    target = TargetAllocation()
    assert target_to_dto(target) == {"assets": []}


def test_target_to_dto_sorted_by_id() -> None:
    target = TargetAllocation()

    # Add in non-sorted order
    target.add_asset(
        Asset(id="b", name="B", purpose="growth"), 0.2, {"lower": 0.1, "upper": 0.3}
    )
    target.add_asset(
        Asset(id="a", name="A", purpose="growth"), 0.3, {"lower": 0.2, "upper": 0.4}
    )
    target.add_asset(
        Asset(id="c", name="C", purpose="hedge"), 0.5, {"lower": 0.4, "upper": 0.6}
    )

    dto = target_to_dto(target)
    assert [a["id"] for a in dto["assets"]] == ["a", "b", "c"]


def test_target_to_dto_field_mapping() -> None:
    target = TargetAllocation()
    target.add_asset(
        Asset(id="spy", name="S&P500", purpose="growth"),
        0.6,
        {"lower": 0.55, "upper": 0.65},
    )

    dto = target_to_dto(target)
    assert dto == {
        "assets": [
            {
                "id": "spy",
                "name": "S&P500",
                "purpose": "growth",
                "target_ratio": 0.6,
                "tolerance": {"lower": 0.55, "upper": 0.65},
            }
        ]
    }


# ---------------------------------------------------------------------------
# dto_to_target (schema already validated in save/load)
# ---------------------------------------------------------------------------


def test_dto_to_target_valid() -> None:
    dto = {
        "assets": [
            make_asset_dto(asset_id="a", target_ratio=0.3, lower=0.2, upper=0.4),
            make_asset_dto(asset_id="b", target_ratio=0.7, lower=0.6, upper=0.8),
        ]
    }

    target = dto_to_target(dto)  # type: ignore[arg-type]
    assert normalize_target(target) == {
        "a": (0.3, {"lower": 0.2, "upper": 0.4}),
        "b": (0.7, {"lower": 0.6, "upper": 0.8}),
    }


def test_dto_to_target_duplicate_asset_raises() -> None:
    dto = {
        "assets": [
            make_asset_dto(asset_id="dup", target_ratio=0.5),
            make_asset_dto(asset_id="dup", target_ratio=0.5),
        ]
    }

    with pytest.raises(DuplicateAssetError):
        dto_to_target(dto)  # type: ignore[arg-type]


@pytest.mark.parametrize("bad_ratio", [-0.01, 1.01])
def test_dto_to_target_invalid_target_ratio_raises(bad_ratio: float) -> None:
    dto = {"assets": [make_asset_dto(asset_id="a", target_ratio=bad_ratio)]}

    with pytest.raises(InvalidTargetRatioError):
        dto_to_target(dto)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "lower, upper",
    [
        (0.7, 0.6),  # lower > upper
        (-0.1, 0.2),  # lower < 0
        (0.2, 1.1),  # upper > 1
    ],
)
def test_dto_to_target_invalid_tolerance_bounds_raises(
    lower: float, upper: float
) -> None:
    dto = {
        "assets": [
            make_asset_dto(asset_id="a", target_ratio=0.5, lower=lower, upper=upper)
        ]
    }

    with pytest.raises(InvalidToleranceBoundsError):
        dto_to_target(dto)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Round-trip
# ---------------------------------------------------------------------------


def test_roundtrip_domain_to_dto_to_domain() -> None:
    t1 = TargetAllocation()
    t1.add_asset(
        Asset(id="b", name="B", purpose="growth"), 0.2, {"lower": 0.1, "upper": 0.3}
    )
    t1.add_asset(
        Asset(id="a", name="A", purpose="growth"), 0.3, {"lower": 0.2, "upper": 0.4}
    )
    t1.add_asset(
        Asset(id="c", name="C", purpose="hedge"), 0.5, {"lower": 0.4, "upper": 0.6}
    )

    dto = target_to_dto(t1)
    t2 = dto_to_target(dto)  # type: ignore[arg-type]

    assert normalize_target(t2) == normalize_target(t1)


def test_roundtrip_dto_to_domain_to_dto_sorted() -> None:
    # Shuffled order on purpose (schema-valid)
    dto1: TargetAllocationDTO = {
        "assets": [
            make_asset_dto(asset_id="c", target_ratio=0.5, lower=0.4, upper=0.6),
            make_asset_dto(asset_id="a", target_ratio=0.3, lower=0.2, upper=0.4),
            make_asset_dto(asset_id="b", target_ratio=0.2, lower=0.1, upper=0.3),
        ]
    }

    target = dto_to_target(dto1)  # type: ignore[arg-type]
    dto2 = target_to_dto(target)

    # ordering is deterministic by id
    assert [a["id"] for a in dto2["assets"]] == ["a", "b", "c"]

    # content matches ignoring order
    assert norm_dto_assets(dto2) == norm_dto_assets(dto1)
