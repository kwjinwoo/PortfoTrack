from typing import TypedDict

from portfotrack.domain.optional_bet import (
    CapBreachResult,
    OptionalBetSnapshot,
)
from portfotrack.domain.optional_bet.optional_bet import (
    check_cap_breaches as domain_check_cap_breaches,
)
from portfotrack.path import OPTIONAL_BETS_DIR
from portfotrack.services.snapshot_services import (
    load_latest_snapshot,
    load_snapshot_by_filename,
)
from portfotrack.storage.json_store.errors import OptionalBetNotFoundError
from portfotrack.storage.json_store.optional_bet_store import load as store_load
from portfotrack.storage.json_store.optional_bet_store import save as store_save
from portfotrack.storage.json_store.optional_bet_store import (
    save_to_file as store_save_to_file,
)
from portfotrack.storage.serialization.optional_bet_json import (
    dto_to_optional_bet,
    optional_bet_to_dto,
)


def init_optional_bet_snapshot() -> OptionalBetSnapshot:
    """Create a new, empty OptionalBetSnapshot.

    Returns:
        A fresh OptionalBetSnapshot instance ready for items to be added.
    """
    return OptionalBetSnapshot()


def add_item(
    snapshot: OptionalBetSnapshot,
    asset_id: str,
    name: str,
    cap_ratio: float,
    amount: int,
) -> OptionalBetSnapshot:
    """Add an optional bet item to the snapshot.

    Delegates validation and mutation to the domain model.

    Args:
        snapshot: The OptionalBetSnapshot to modify.
        asset_id: Unique identifier for the asset.
        name: Human-readable display name.
        cap_ratio: Maximum allowed ratio in (0.0, 1.0).
        amount: Holding amount in KRW.

    Returns:
        The same OptionalBetSnapshot instance (mutated).

    Raises:
        DuplicateOptionalBetError: If asset_id already exists.
        InvalidCapRatioError: If cap_ratio is not in (0.0, 1.0).
        ValueError: If amount is negative.
    """
    snapshot.add_item(asset_id, name, cap_ratio, amount)
    return snapshot


def remove_item(
    snapshot: OptionalBetSnapshot,
    asset_id: str,
) -> OptionalBetSnapshot:
    """Remove an optional bet item from the snapshot by asset_id.

    Args:
        snapshot: The OptionalBetSnapshot to modify.
        asset_id: The identifier of the item to remove.

    Returns:
        The same OptionalBetSnapshot instance (mutated).

    Raises:
        OptionalBetAssetNotFoundError: If no item with the given
            asset_id exists.
    """
    snapshot.remove_item(asset_id)
    return snapshot


def update_item(
    snapshot: OptionalBetSnapshot,
    asset_id: str,
    *,
    name: str | None = None,
    cap_ratio: float | None = None,
    amount: int | None = None,
) -> OptionalBetSnapshot:
    """Update fields of an existing optional bet item.

    Only the provided keyword arguments are updated; others retain
    their current values. Delegates validation to the domain model.

    Args:
        snapshot: The OptionalBetSnapshot to modify.
        asset_id: The identifier of the item to update.
        name: New display name, or None to keep current.
        cap_ratio: New cap ratio in (0.0, 1.0), or None to keep current.
        amount: New amount (non-negative), or None to keep current.

    Returns:
        The same OptionalBetSnapshot instance (mutated).

    Raises:
        OptionalBetAssetNotFoundError: If no item with the given
            asset_id exists.
        InvalidCapRatioError: If cap_ratio is not in (0.0, 1.0).
        ValueError: If amount is negative.
    """
    snapshot.update_item(asset_id, name=name, cap_ratio=cap_ratio, amount=amount)
    return snapshot


def save_optional_bet(snapshot: OptionalBetSnapshot) -> None:
    """Persist an optional bet snapshot to disk.

    Converts the domain object to a DTO and delegates to the storage layer.

    Args:
        snapshot: The OptionalBetSnapshot to persist.
    """
    dto = optional_bet_to_dto(snapshot)
    store_save(dto)


def save_optional_bet_overwrite(snapshot: OptionalBetSnapshot, file_name: str) -> None:
    """Persist an optional bet snapshot to a specific file, overwriting it.

    Args:
        snapshot: The OptionalBetSnapshot to persist.
        file_name: Target file name to overwrite.
    """
    dto = optional_bet_to_dto(snapshot)
    store_save_to_file(dto, file_name)


def load_latest_optional_bet() -> OptionalBetSnapshot:
    """Load the most recent optional bet snapshot from disk.

    Scans the optional bets directory for files matching the pattern
    ``optional_bet_*.json``, sorts by filename descending, and loads
    the most recent one.

    Returns:
        The OptionalBetSnapshot from the latest file.

    Raises:
        OptionalBetNotFoundError: If no optional bet file exists.
    """
    bet_files = sorted(OPTIONAL_BETS_DIR.glob("optional_bet_*.json"), reverse=True)

    if not bet_files:
        raise OptionalBetNotFoundError(file_name="optional_bet_*.json")

    latest_file_name = bet_files[0].name
    dto = store_load(latest_file_name)
    return dto_to_optional_bet(dto)


def check_cap_breaches(
    snapshot: OptionalBetSnapshot, *, main_portfolio_total: int
) -> list[CapBreachResult]:
    """Check which optional bet items exceed their individual cap ratios.

    Delegates to the domain-level pure function.

    Args:
        snapshot: Optional bet snapshot to check.
        main_portfolio_total: Total amount of the main portfolio in KRW.

    Returns:
        List of CapBreachResult for items exceeding their cap.
    """
    return domain_check_cap_breaches(
        snapshot.items, main_portfolio_total=main_portfolio_total
    )


class CapBreachReport(TypedDict):
    """Result of a snapshot-based cap breach check."""

    breaches: list[CapBreachResult]
    snapshot_date: str
    main_portfolio_total: int


def check_cap_breaches_with_snapshot(
    snapshot_filename: str | None = None,
) -> CapBreachReport:
    """Check cap breaches using a portfolio snapshot for the main total.

    Loads the latest optional bet snapshot and a portfolio snapshot,
    computes the main portfolio total from the snapshot's items, then
    delegates to the domain-level breach check.

    Args:
        snapshot_filename: Optional snapshot file name. When ``None``,
            the latest snapshot is used.

    Returns:
        A CapBreachReport containing breaches, snapshot date, and the
        computed main portfolio total.

    Raises:
        SnapshotNotFoundError: If the requested snapshot does not exist.
        OptionalBetNotFoundError: If no optional bet snapshot exists.
    """
    if snapshot_filename is not None:
        portfolio = load_snapshot_by_filename(snapshot_filename)
    else:
        portfolio = load_latest_snapshot()

    ob_snapshot = load_latest_optional_bet()
    main_portfolio_total = sum(item.amount for item in portfolio.items)

    breaches = domain_check_cap_breaches(
        ob_snapshot.items, main_portfolio_total=main_portfolio_total
    )

    return CapBreachReport(
        breaches=breaches,
        snapshot_date=portfolio.date,
        main_portfolio_total=main_portfolio_total,
    )
