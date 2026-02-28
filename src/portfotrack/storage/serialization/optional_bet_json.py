from typing import TypedDict

from portfotrack.domain.optional_bet import OptionalBetSnapshot


class OptionalBetItemDTO(TypedDict):
    asset_id: str
    name: str
    cap_ratio: float
    amount: int


class OptionalBetSnapshotDTO(TypedDict):
    date: str
    currency: str
    items: list[OptionalBetItemDTO]


def optional_bet_to_dto(snapshot: OptionalBetSnapshot) -> OptionalBetSnapshotDTO:
    """Convert an OptionalBetSnapshot domain object into a JSON-serializable DTO.

    Items are sorted by asset_id for deterministic output, which is useful
    for diffs and reproducible file persistence.

    Args:
        snapshot: The OptionalBetSnapshot domain object to convert.

    Returns:
        An OptionalBetSnapshotDTO containing date, currency, and sorted items.
    """
    items: list[OptionalBetItemDTO] = []

    sorted_items = sorted(snapshot.items, key=lambda item: item.asset_id)

    for item in sorted_items:
        item_dto: OptionalBetItemDTO = {
            "asset_id": item.asset_id,
            "name": item.name,
            "cap_ratio": item.cap_ratio,
            "amount": item.amount,
        }
        items.append(item_dto)

    return {"date": snapshot.date, "currency": snapshot.currency, "items": items}


def dto_to_optional_bet(dto: OptionalBetSnapshotDTO) -> OptionalBetSnapshot:
    """Convert an OptionalBetSnapshotDTO into an OptionalBetSnapshot domain object.

    Reconstructs domain objects from a DTO, typically loaded from a JSON file.
    Validates each item strictly as invariant checks.

    Args:
        dto: The OptionalBetSnapshotDTO to convert.

    Returns:
        An OptionalBetSnapshot domain object reconstructed from the DTO.
    """
    snapshot = OptionalBetSnapshot(date=dto["date"], currency=dto["currency"])

    for item_dto in dto["items"]:
        asset_id, name, cap_ratio, amount = _parse_item_dto(item_dto)
        snapshot.add_item(asset_id, name, cap_ratio, amount)

    return snapshot


def _parse_item_dto(
    item_dto: OptionalBetItemDTO,
) -> tuple[str, str, float, int]:
    """Parse and validate a single optional bet item DTO.

    All checks are strict and treated as invariants, as the DTO is
    expected to originate from trusted save logic.

    Args:
        item_dto: A dictionary representing a serialized optional bet item.

    Returns:
        A tuple containing (asset_id, name, cap_ratio, amount).

    Raises:
        TypeError: If the DTO or any of its fields has an unexpected type.
        RuntimeError: If required keys are missing.
    """
    if not isinstance(item_dto, dict):
        raise TypeError(
            f"Invariant violated: item dto must be a dict, "
            f"got {type(item_dto).__name__}."
        )

    for key in ("asset_id", "name", "cap_ratio", "amount"):
        if key not in item_dto:
            raise RuntimeError(
                f"Invariant violated: item dto missing key '{key}'. "
                "This indicates a bug in save logic."
            )

    asset_id = item_dto["asset_id"]
    name = item_dto["name"]
    cap_ratio = item_dto["cap_ratio"]
    amount = item_dto["amount"]

    if not isinstance(asset_id, str) or not asset_id:
        raise TypeError("Invariant violated: 'asset_id' must be a non-empty string.")
    if not isinstance(name, str) or not name:
        raise TypeError("Invariant violated: 'name' must be a non-empty string.")
    if not isinstance(cap_ratio, (int, float)) or isinstance(cap_ratio, bool):
        raise TypeError("Invariant violated: 'cap_ratio' must be a number.")
    if not isinstance(amount, int) or isinstance(amount, bool):
        raise TypeError("Invariant violated: 'amount' must be an int.")

    return (asset_id, name, float(cap_ratio), amount)
