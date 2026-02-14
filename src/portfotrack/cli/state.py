import threading
from dataclasses import dataclass

from portfotrack.domain.snapshot import Snapshot
from portfotrack.domain.target_allocation import TargetAllocation


@dataclass(slots=True)
class ReplState:
    """In-memory state for the PortfoTrack REPL session.

    This state is ephemeral (not persisted automatically). Command handlers
    mutate this object to reflect the current interactive session context.

    Attributes:
        target: The currently active target allocation. None means no target
            has been initialized or loaded yet.
        snapshot: The currently active snapshot. None means no snapshot has been
            initialized or loaded yet.
        web_server_thread: Reference to the running web server thread. None if
            the web server has not been started or has been stopped.
    """

    target: TargetAllocation | None = None
    snapshot: Snapshot | None = None
    web_server_thread: threading.Thread | None = None
