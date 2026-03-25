"""Domain-specific exception hierarchy for the banking system.

All service-layer errors are expressed as subclasses of DomainException.
Each layer catches and re-raises with added context; stack traces are
never exposed in HTTP responses.
"""

from __future__ import annotations


class DomainException(Exception):
    """Base class for all domain-specific exceptions."""


class NotFoundException(DomainException):
    """Raised when a requested resource cannot be found."""

    def __init__(self, resource: str) -> None:
        self.resource = resource
        super().__init__(f"{resource} not found.")


class UnauthorizedException(DomainException):
    """Raised for unauthenticated access attempts."""

    def __init__(self, message: str = "Unauthorized access.") -> None:
        super().__init__(message)


class InvalidCredentialsException(DomainException):
    """Raised when supplied credentials are invalid."""

    def __init__(self, message: str = "Invalid credentials.") -> None:
        super().__init__(message)


class ValidationException(DomainException):
    """Raised for request-payload validation errors."""

    def __init__(self, errors: dict) -> None:
        self.errors = errors
        super().__init__(f"Validation errors occurred: {errors}")


class ConflictException(DomainException):
    """Raised for conflicts in the application state."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class InsufficientPermissionsException(DomainException):
    """Raised when an authenticated user attempts an action they are not authorised to perform."""

    def __init__(self, message: str = "Insufficient permissions.") -> None:
        super().__init__(message)


class AccountNotFoundException(DomainException):
    """Raised when a bank account cannot be found or is soft-deleted."""

    def __init__(self, account_number: str) -> None:
        self.account_number = account_number
        super().__init__(f"Account {account_number} not found.")


class AccountAlreadyClosedException(DomainException):
    """Raised when an operation is attempted on an already-closed account."""

    def __init__(self, account_number: str) -> None:
        self.account_number = account_number
        super().__init__(f"Account {account_number} is already closed.")


class AccountTypeNotFoundException(DomainException):
    """Raised when the authenticated user has no active account for the requested type."""

    def __init__(self, account_type: str) -> None:
        self.account_type = account_type
        super().__init__(f"No active {account_type} account found for this user.")


class UserProfileNotFoundException(NotFoundException):
    """Raised when a user profile cannot be found for the given owner.

    Attributes:
        owner_id: The owner ID for which no profile was found.
    """

    def __init__(self, owner_id: str) -> None:
        """Initialise with the owner ID that was not found.

        Args:
            owner_id: The JWT sub of the profile owner.
        """
        self.owner_id = owner_id
        super().__init__(resource="UserProfile")


class RepositoryException(DomainException):
    """Raised when a repository-layer operation fails.

    Wraps underlying data-store errors so Cosmos SDK exceptions
    never escape the repository boundary.
    """

    def __init__(self, message: str, cause: Exception | None = None) -> None:
        self.cause = cause
        super().__init__(message)
