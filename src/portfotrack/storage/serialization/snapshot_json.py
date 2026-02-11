from typing import TypedDict

from portfotrack.domain.snapshot import Snapshot


class SnapshotItemDTO(TypedDict):
    asset_id: str
    label: str
    amount: int


class SnapshotDTO(TypedDict):
    date: str
    currency: str
    items: list[SnapshotItemDTO]


def snapshot_to_dto(snapshot: Snapshot) -> SnapshotDTO:
    """Convert a Snapshot domain object into a JSON-serializable DTO.

    This function transforms the domain representation into a stable,
    JSON-friendly structure. Item order is preserved as-is, since
    insertion order carries meaning (user's entry order).

    Args:
        snapshot: The Snapshot domain object to convert.

    Returns:
        A SnapshotDTO dictionary containing date, currency, and a list
        of items with their asset_id, label, and amount.
    """
    items: list[SnapshotItemDTO] = []
    for item in snapshot.items:
        item_dto: SnapshotItemDTO = {
            "asset_id": item.asset_id,
            "label": item.label,
            "amount": item.amount,
        }
        items.append(item_dto)

    return {"date": snapshot.date, "currency": snapshot.currency, "items": items}


def dto_to_snapshot(dto: SnapshotDTO) -> Snapshot:
    """Convert a SnapshotDTO into a Snapshot domain object.

    This function reconstructs domain objects from a DTO, typically loaded
    from a JSON file. It assumes the top-level DTO structure matches the
    expected schema, but validates each item strictly.

    Args:
        dto: The SnapshotDTO to convert.

    Returns:
        A Snapshot domain object reconstructed from the DTO.
    """
    snapshot = Snapshot(date=dto["date"], currency=dto["currency"])

    for item_dto in dto["items"]:
        asset_id, label, amount = _parse_snapshot_item_dto(item_dto)
        snapshot.add_snapshot_item(asset_id, label, amount)

    return snapshot


def _parse_snapshot_item_dto(item_dto: SnapshotItemDTO) -> tuple[str, str, int]:
    """Parse and validate a single snapshot item DTO.

    This function validates the structure and types of a snapshot item DTO
    loaded from JSON and extracts the fields required to construct a
    SnapshotItem. All checks are strict and treated as invariants, as the
    DTO is expected to originate from trusted save logic.

    Args:
        item_dto: A dictionary representing a serialized snapshot item.

    Returns:
        A tuple containing:
            - asset_id: Asset class identifier.
            - label: Human-readable label for the holding.
            - amount: Absolute amount in the snapshot currency.

    Raises:
        TypeError: If the DTO or any of its fields has an unexpected type.
        RuntimeError: If required keys are missing, indicating a bug in the
            save logic.
    """
    if not isinstance(item_dto, dict):
        raise TypeError(
            f"Invariant violated: item dto must be a dict, got {type(item_dto).__name__}."
        )

    for key in ("asset_id", "label", "amount"):
        if key not in item_dto:
            raise RuntimeError(
                f"Invariant violated: item dto missing key '{key}'. "
                "This indicates a bug in save logic."
            )

    asset_id = item_dto["asset_id"]
    label = item_dto["label"]
    amount = item_dto["amount"]

    if not isinstance(asset_id, str) or not asset_id:
        raise TypeError("Invariant violated: 'asset_id' must be a non-empty string.")
    if not isinstance(label, str) or not label:
        raise TypeError("Invariant violated: 'label' must be a non-empty string.")
    if not isinstance(amount, int) or isinstance(amount, bool):
        raise TypeError("Invariant violated: 'amount' must be an int.")

    return (asset_id, label, amount)
