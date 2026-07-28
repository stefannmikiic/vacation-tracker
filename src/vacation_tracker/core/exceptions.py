"""Application-level exceptions."""


class ImportStructureError(Exception):
    """Raised when an import file is missing required metadata or headers."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class OverlappingUsageError(Exception):
    """Raised when a new usage overlaps an existing one for the same employee."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class InsufficientBalanceError(Exception):
    """Raised when creating a usage would make yearly available days negative."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class MissingAllowanceError(Exception):
    """Raised when a usage touches a year with no vacation allowance."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)
