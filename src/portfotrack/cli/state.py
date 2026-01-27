from dataclasses import dataclass

from portfotrack.domain.target_allocation import TargetAllocation


@dataclass(slots=True)
class ReplState:
    """In-memory state for the PortfoTrack REPL session.

    This state is ephemeral (not persisted automatically). Command handlers
    mutate this object to reflect the current interactive session context.

    Attributes:
        target: The currently active target allocation. None means no target
            has been initialized or loaded yet.
    """

    target: TargetAllocation | None = None
