"""Unit tests for src/exceptions/domain_exceptions.py.

Verifies exception hierarchy, message formatting, and attribute assignment
for every exception class in the domain exception module.
"""

from __future__ import annotations

import pytest

from src.exceptions.domain_exceptions import (
    AccountAlreadyClosedException,
    AccountNotFoundException,
    ConflictException,
    DomainException,
    InsufficientPermissionsException,
    InvalidCredentialsException,
    NotFoundException,
    RepositoryException,
    UnauthorizedException,
    ValidationException,
)


class TestDomainException:
    """Tests for the base DomainException class."""

    def test_domain_exception_is_exception_subclass(self) -> None:
        assert issubclass(DomainException, Exception)

    def test_domain_exception_can_be_raised_and_caught(self) -> None:
        with pytest.raises(DomainException):
            raise DomainException("base error")


class TestNotFoundException:
    """Tests for NotFoundException."""

    def test_not_found_exception_is_domain_exception(self) -> None:
        assert issubclass(NotFoundException, DomainException)

    def test_not_found_exception_stores_resource(self) -> None:
        exc = NotFoundException("Account")
        assert exc.resource == "Account"

    def test_not_found_exception_message_includes_resource(self) -> None:
        exc = NotFoundException("Order")
        assert "Order" in str(exc)
        assert "not found" in str(exc)


class TestUnauthorizedException:
    """Tests for UnauthorizedException."""

    def test_unauthorized_exception_is_domain_exception(self) -> None:
        assert issubclass(UnauthorizedException, DomainException)

    def test_unauthorized_exception_default_message(self) -> None:
        exc = UnauthorizedException()
        assert "Unauthorized" in str(exc)

    def test_unauthorized_exception_custom_message(self) -> None:
        exc = UnauthorizedException("Token expired.")
        assert str(exc) == "Token expired."


class TestInvalidCredentialsException:
    """Tests for InvalidCredentialsException."""

    def test_invalid_credentials_exception_is_domain_exception(self) -> None:
        assert issubclass(InvalidCredentialsException, DomainException)

    def test_invalid_credentials_exception_default_message(self) -> None:
        exc = InvalidCredentialsException()
        assert "Invalid credentials" in str(exc)

    def test_invalid_credentials_exception_custom_message(self) -> None:
        exc = InvalidCredentialsException("Bad password.")
        assert str(exc) == "Bad password."


class TestValidationException:
    """Tests for ValidationException."""

    def test_validation_exception_is_domain_exception(self) -> None:
        assert issubclass(ValidationException, DomainException)

    def test_validation_exception_stores_errors_dict(self) -> None:
        errors = {"field": "required"}
        exc = ValidationException(errors)
        assert exc.errors == errors

    def test_validation_exception_message_includes_errors(self) -> None:
        errors = {"amount": "must be positive"}
        exc = ValidationException(errors)
        assert "amount" in str(exc)


class TestConflictException:
    """Tests for ConflictException."""

    def test_conflict_exception_is_domain_exception(self) -> None:
        assert issubclass(ConflictException, DomainException)

    def test_conflict_exception_message_is_preserved(self) -> None:
        exc = ConflictException("Duplicate account.")
        assert str(exc) == "Duplicate account."


class TestInsufficientPermissionsException:
    """Tests for InsufficientPermissionsException."""

    def test_insufficient_permissions_is_domain_exception(self) -> None:
        assert issubclass(InsufficientPermissionsException, DomainException)

    def test_insufficient_permissions_default_message(self) -> None:
        exc = InsufficientPermissionsException()
        assert "permissions" in str(exc).lower()

    def test_insufficient_permissions_custom_message(self) -> None:
        exc = InsufficientPermissionsException("Admin only.")
        assert str(exc) == "Admin only."


class TestAccountNotFoundException:
    """Tests for AccountNotFoundException."""

    def test_account_not_found_is_domain_exception(self) -> None:
        assert issubclass(AccountNotFoundException, DomainException)

    def test_account_not_found_stores_account_number(self) -> None:
        exc = AccountNotFoundException("1234567890")
        assert exc.account_number == "1234567890"

    def test_account_not_found_message_contains_account_number(self) -> None:
        exc = AccountNotFoundException("9999999999")
        assert "9999999999" in str(exc)

    def test_account_not_found_message_contains_not_found(self) -> None:
        exc = AccountNotFoundException("0000000000")
        assert "not found" in str(exc)


class TestAccountAlreadyClosedException:
    """Tests for AccountAlreadyClosedException."""

    def test_account_already_closed_is_domain_exception(self) -> None:
        assert issubclass(AccountAlreadyClosedException, DomainException)

    def test_account_already_closed_stores_account_number(self) -> None:
        exc = AccountAlreadyClosedException("1111111111")
        assert exc.account_number == "1111111111"

    def test_account_already_closed_message_contains_account_number(self) -> None:
        exc = AccountAlreadyClosedException("2222222222")
        assert "2222222222" in str(exc)

    def test_account_already_closed_message_contains_closed(self) -> None:
        exc = AccountAlreadyClosedException("0000000000")
        assert "closed" in str(exc).lower()


class TestRepositoryException:
    """Tests for RepositoryException."""

    def test_repository_exception_is_domain_exception(self) -> None:
        assert issubclass(RepositoryException, DomainException)

    def test_repository_exception_message_is_preserved(self) -> None:
        exc = RepositoryException("Cosmos write failed.")
        assert str(exc) == "Cosmos write failed."

    def test_repository_exception_cause_defaults_to_none(self) -> None:
        exc = RepositoryException("Error.")
        assert exc.cause is None

    def test_repository_exception_stores_cause(self) -> None:
        cause = ValueError("upstream")
        exc = RepositoryException("Wrapped error.", cause=cause)
        assert exc.cause is cause

    def test_repository_exception_can_be_raised_and_caught_as_domain_exception(
        self,
    ) -> None:
        with pytest.raises(DomainException):
            raise RepositoryException("fail")
