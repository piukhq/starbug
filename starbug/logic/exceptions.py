"""Custom exceptions for the Starbug Application."""

class NamespaceRequiredError(Exception):
    """Exception raised when a namespace is required but not provided."""

    def __init__(self) -> None:
        """Initialize the NamespaceRequiredError class."""
        super().__init__("A namespace is required for this operation.")

class RetryLimitExceededError(Exception):
    """Exception raised when a retry limit is exceeded."""

    def __init__(self) -> None:
        """Initialize the RetryLimitExceededError class."""
        super().__init__("Retry limit exceeded.")
