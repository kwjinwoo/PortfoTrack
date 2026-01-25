import pytest

from portfotrack.domain.asset.asset import Asset


def test__eq__same_instance__returns_true() -> None:
    asset = Asset("id", "same_instance", "test")
    assert asset == asset


@pytest.mark.parametrize(
    "asset1, asset2, expected",
    [
        (
            Asset("id", "name1", "purpose1"),
            Asset("id", "name2", "purpose2"),
            True,
        ),
        (
            Asset("id1", "name", "purpose"),
            Asset("id2", "name", "purpose"),
            False,
        ),
    ],
)
def test__eq__asset_to_asset(asset1: Asset, asset2: Asset, expected: bool) -> None:
    assert (asset1 == asset2) is expected


def test__eq__non_asset__returns_false() -> None:
    asset = Asset("id", "name", "purpose")
    non_asset = 32
    assert asset != non_asset


def test__hash_and_eq__same_id_can_lookup_as_dict_key() -> None:
    asset1 = Asset("id", "name1", "purpose1")
    asset2 = Asset("id", "name2", "purpose2")

    d = {asset1: 1}
    assert d[asset2] == 1
