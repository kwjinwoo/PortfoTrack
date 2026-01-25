class AppError(Exception):
    """Base application error with structured metadata.

    This exception provides a stable error code and structured details to enable
    consistent handling across layers (domain, storage, CLI/UI). It is designed
    to support rule-based branching (e.g., retry guidance, user messaging,
    logging, analytics) without relying on fragile string matching.

    Attributes:
        code: Stable machine-readable identifier for the error. Treat as a
            contract that should not change once published.
        message: Human-readable message describing the error. This value is
            also passed to ``Exception`` so standard tooling (tracebacks, logs)
            shows a meaningful message.
        details: Optional structured context for the error, intended for UI/CLI
            guidance, field-level error mapping, and tests. Defaults to an empty
            dict.
        cause: Optional underlying exception that triggered this error. Useful
            for debugging and error chaining.
    """

    def __init__(
        self,
        *,
        code: str,
        message: str,
        details: dict | None = None,
        cause: BaseException | None = None,
    ) -> None:
        """Initializes an AppError.

        Args:
            code: Stable machine-readable identifier for this error.
            message: Human-readable message for this error. This is passed to
                the base ``Exception`` to preserve standard exception behavior.
            details: Optional structured metadata for programmatic handling.
                If ``None``, an empty dict is used.
            cause: Optional underlying exception that caused this error.

        """
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}
        self.cause = cause

    def __str__(self) -> str:
        """Returns a human-friendly string representation.

        Returns:
            A string formatted as ``"[{code}] {message}"``.
        """
        return f"[{self.code}] {self.message}"
