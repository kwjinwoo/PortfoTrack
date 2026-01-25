from dataclasses import dataclass


@dataclass(frozen=True)
class Asset:
    """Represents a logical asset unit in the portfolio.

    An Asset is a domain-level identifier used as a key for portfolio
    targets and snapshots. Assets are considered equal if their `id`
    fields match, regardless of other metadata.

    Attributes:
        id: Stable unique identifier for the asset (e.g. "us_equity").
        name: Human-readable asset name.
        purpose: Descriptive purpose or role of the asset in the portfolio.
    """

    id: str
    name: str
    purpose: str

    def __hash__(self) -> int:
        """Returns a hash value based on the asset identifier.

        The hash is derived solely from `id` so that Asset instances
        with the same logical identity behave consistently as dict keys.

        Returns:
            Hash value of the asset.
        """
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        """Checks equality with another Asset.

        Two Asset objects are considered equal if and only if their
        `id` fields are identical.

        Args:
            other: Object to compare against.

        Returns:
            True if the other object is an Asset with the same id;
            False otherwise.
        """
        if not isinstance(other, Asset):
            return NotImplemented
        return self.id == other.id
