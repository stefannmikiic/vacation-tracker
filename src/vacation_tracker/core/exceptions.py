"""Application-level exceptions."""


class ImportStructureError(Exception):
    """Raised when an import file is missing required metadata or headers."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)
