"""Unit tests for src/services/account_service.py.

All repository interactions are provided via the mock_repo fixture
defined in conftest.py.  No real Cosmos DB connections are made.
"""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import AsyncMock, call, patch

import pytest

from src.exceptions.domain_exceptions import (
    AccountAlreadyClosedException,
    AccountNotFoundException,
    AccountTypeNotFoundException,
    InsufficientPermissionsException,
)
from src.models.account import (
    AccountAdminResponse,
    AccountBalanceResponse,
    AccountCloseRequest,
    AccountCreate,
    AccountResponse,
    AccountStatus,
    AccountType,
    AccountUpdate,
)
from src.services.account_service import AccountService

from tests.conftest import (
    ACCOUNT_NUMBER,
    CLOSED_DOC,
    OTHER_OWNER_ID,
    OWNER_ID,
    make_account_doc,
)


class TestGenerateAccountNumber:
    """Tests for AccountService._generate_account_number()."""

    def test_generate_account_number_returns_string(self) -> None:
        result = AccountService._generate_account_number()
        assert isinstance(result, str)

    def test_generate_account_number_is_ten_characters(self) -> None:
        result = AccountService._generate_account_number()
        assert len(result) == 10

    def test_generate_account_number_contains_only_digits(self) -> None:
        result = AccountService._generate_account_number()
        assert result.isdigit()

    def test_generate_account_number_is_zero_padded(self) -> None:
        # Force a short int so zero-padding is exercised
        with patch("src.services.account_service.uuid") as mock_uuid:
            mock_uuid.uuid4.return_value.int = 42
            result = AccountService._generate_account_number()
        assert result == "0000000042"


class TestCreateAccount:
    """Tests for AccountService.create_account()."""

    @pytest.mark.asyncio
    async def test_create_account_calls_repo_create_once(
        self, account_service: AccountService, mock_repo: AsyncMock
    ) -> None:
        payload = AccountCreate(account_type=AccountType.SAVINGS)
        await account_service.create_account(payload, OWNER_ID)
        mock_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_account_passes_owner_id_to_repo(
        self, account_service: AccountService, mock_repo: AsyncMock
    ) -> None:
        payload = AccountCreate(account_type=AccountType.SAVINGS)
        await account_service.create_account(payload, OWNER_ID)
        created_doc = mock_repo.create.call_args[0][0]
        assert created_doc["owner_id"] == OWNER_ID

    @pytest.mark.asyncio
    async def test_create_account_returns_account_response(
        self, account_service: AccountService, mock_repo: AsyncMock
    ) -> None:
        payload = AccountCreate(account_type=AccountType.CURRENT)
        result = await account_service.create_account(payload, OWNER_ID)
        assert isinstance(result, AccountResponse)

    @pytest.mark.asyncio
    async def test_create_account_uppercases_currency(
        self, account_service: AccountService, mock_repo: AsyncMock
    ) -> None:
        payload = AccountCreate(account_type=AccountType.SAVINGS, currency="gbp")
        await account_service.create_account(payload, OWNER_ID)
        created_doc = mock_repo.create.call_args[0][0]
        assert created_doc["currency"] == "GBP"

    @pytest.mark.asyncio
    async def test_create_account_sets_status_active(
        self, account_service: AccountService, mock_repo: AsyncMock
    ) -> None:
        payload = AccountCreate(account_type=AccountType.SAVINGS)
        await account_service.create_account(payload, OWNER_ID)
        created_doc = mock_repo.create.call_args[0][0]
        assert created_doc["status"] == AccountStatus.ACTIVE.value

    @pytest.mark.asyncio
    async def test_create_account_sets_is_deleted_false(
        self, account_service: AccountService, mock_repo: AsyncMock
    ) -> None:
        payload = AccountCreate(account_type=AccountType.SAVINGS)
        await account_service.create_account(payload, OWNER_ID)
        created_doc = mock_repo.create.call_args[0][0]
        assert created_doc["is_deleted"] is False


class TestGetAccount:
    """Tests for AccountService.get_account()."""

    @pytest.mark.asyncio
    async def test_get_account_success_returns_account_response(
        self, account_service: AccountService, mock_repo: AsyncMock
    ) -> None:
        mock_repo.get_by_account_number.return_value = make_account_doc()
        result = await account_service.get_account(ACCOUNT_NUMBER, OWNER_ID)
        assert isinstance(result, AccountResponse)

    @pytest.mark.asyncio
    async def test_get_account_success_returns_correct_account_number(
        self, account_service: AccountService, mock_repo: AsyncMock
    ) -> None:
        mock_repo.get_by_account_number.return_value = make_account_doc()
        result = await account_service.get_account(ACCOUNT_NUMBER, OWNER_ID)
        assert result.account_number == ACCOUNT_NUMBER

    @pytest.mark.asyncio
    async def test_get_account_missing_doc_raises_account_not_found(
        self, account_service: AccountService, mock_repo: AsyncMock
    ) -> None:
        mock_repo.get_by_account_number.return_value = None
        with pytest.raises(AccountNotFoundException):
            await account_service.get_account(ACCOUNT_NUMBER, OWNER_ID)

    @pytest.mark.asyncio
    async def test_get_account_deleted_doc_raises_account_not_found(
        self, account_service: AccountService, mock_repo: AsyncMock
    ) -> None:
        mock_repo.get_by_account_number.return_value = CLOSED_DOC
        with pytest.raises(AccountNotFoundException):
            await account_service.get_account(ACCOUNT_NUMBER, OWNER_ID)

    @pytest.mark.asyncio
    async def test_get_account_wrong_owner_raises_insufficient_permissions(
        self, account_service: AccountService, mock_repo: AsyncMock
    ) -> None:
        mock_repo.get_by_account_number.return_value = make_account_doc(
            owner_id=OTHER_OWNER_ID
        )
        with pytest.raises(InsufficientPermissionsException):
            await account_service.get_account(ACCOUNT_NUMBER, OWNER_ID)


class TestListAccounts:
    """Tests for AccountService.list_accounts()."""

    @pytest.mark.asyncio
    async def test_list_accounts_calls_list_by_owner(
        self, account_service: AccountService, mock_repo: AsyncMock
    ) -> None:
        mock_repo.list_by_owner.return_value = [make_account_doc()]
        await account_service.list_accounts(OWNER_ID)
        mock_repo.list_by_owner.assert_called_once_with(OWNER_ID, include_closed=False)

    @pytest.mark.asyncio
    async def test_list_accounts_returns_list_of_account_response(
        self, account_service: AccountService, mock_repo: AsyncMock
    ) -> None:
        mock_repo.list_by_owner.return_value = [
            make_account_doc(),
            make_account_doc(account_number="9999999999"),
        ]
        result = await account_service.list_accounts(OWNER_ID)
        assert len(result) == 2
        assert all(isinstance(a, AccountResponse) for a in result)

    @pytest.mark.asyncio
    async def test_list_accounts_returns_empty_list_when_none(
        self, account_service: AccountService, mock_repo: AsyncMock
    ) -> None:
        mock_repo.list_by_owner.return_value = []
        result = await account_service.list_accounts(OWNER_ID)
        assert result == []


class TestUpdateAccount:
    """Tests for AccountService.update_account()."""

    @pytest.mark.asyncio
    async def test_update_account_success_returns_account_response(
        self, account_service: AccountService, mock_repo: AsyncMock
    ) -> None:
        mock_repo.get_by_account_number.return_value = make_account_doc()
        mock_repo.update.return_value = make_account_doc()
        payload = AccountUpdate(currency="EUR")
        result = await account_service.update_account(ACCOUNT_NUMBER, payload, OWNER_ID)
        assert isinstance(result, AccountResponse)

    @pytest.mark.asyncio
    async def test_update_account_uppercases_currency(
        self, account_service: AccountService, mock_repo: AsyncMock
    ) -> None:
        mock_repo.get_by_account_number.return_value = make_account_doc()
        mock_repo.update.return_value = make_account_doc()
        payload = AccountUpdate(currency="eur")
        await account_service.update_account(ACCOUNT_NUMBER, payload, OWNER_ID)
        updates = mock_repo.update.call_args[0][1]
        assert updates["currency"] == "EUR"

    @pytest.mark.asyncio
    async def test_update_account_no_currency_does_not_include_currency_in_updates(
        self, account_service: AccountService, mock_repo: AsyncMock
    ) -> None:
        mock_repo.get_by_account_number.return_value = make_account_doc()
        mock_repo.update.return_value = make_account_doc()
        payload = AccountUpdate()
        await account_service.update_account(ACCOUNT_NUMBER, payload, OWNER_ID)
        updates = mock_repo.update.call_args[0][1]
        assert "currency" not in updates

    @pytest.mark.asyncio
    async def test_update_account_not_found_raises_account_not_found(
        self, account_service: AccountService, mock_repo: AsyncMock
    ) -> None:
        mock_repo.get_by_account_number.return_value = None
        with pytest.raises(AccountNotFoundException):
            await account_service.update_account(
                ACCOUNT_NUMBER, AccountUpdate(), OWNER_ID
            )

    @pytest.mark.asyncio
    async def test_update_account_wrong_owner_raises_insufficient_permissions(
        self, account_service: AccountService, mock_repo: AsyncMock
    ) -> None:
        mock_repo.get_by_account_number.return_value = make_account_doc(
            owner_id=OTHER_OWNER_ID
        )
        with pytest.raises(InsufficientPermissionsException):
            await account_service.update_account(
                ACCOUNT_NUMBER, AccountUpdate(), OWNER_ID
            )

    @pytest.mark.asyncio
    async def test_update_account_closed_raises_account_already_closed(
        self, account_service: AccountService, mock_repo: AsyncMock
    ) -> None:
        closed = make_account_doc(status=AccountStatus.CLOSED.value, is_deleted=False)
        mock_repo.get_by_account_number.return_value = closed
        with pytest.raises(AccountAlreadyClosedException):
            await account_service.update_account(
                ACCOUNT_NUMBER, AccountUpdate(), OWNER_ID
            )


class TestCloseAccount:
    """Tests for AccountService.close_account()."""

    @pytest.mark.asyncio
    async def test_close_account_success_returns_account_response(
        self, account_service: AccountService, mock_repo: AsyncMock
    ) -> None:
        mock_repo.get_by_account_number.return_value = make_account_doc()
        mock_repo.update.return_value = CLOSED_DOC
        payload = AccountCloseRequest(closure_reason="No longer needed.")
        result = await account_service.close_account(ACCOUNT_NUMBER, payload, OWNER_ID)
        assert isinstance(result, AccountResponse)

    @pytest.mark.asyncio
    async def test_close_account_sets_is_deleted_true_in_updates(
        self, account_service: AccountService, mock_repo: AsyncMock
    ) -> None:
        mock_repo.get_by_account_number.return_value = make_account_doc()
        mock_repo.update.return_value = CLOSED_DOC
        payload = AccountCloseRequest(closure_reason="Closing account now.")
        await account_service.close_account(ACCOUNT_NUMBER, payload, OWNER_ID)
        updates = mock_repo.update.call_args[0][1]
        assert updates["is_deleted"] is True

    @pytest.mark.asyncio
    async def test_close_account_sets_status_closed_in_updates(
        self, account_service: AccountService, mock_repo: AsyncMock
    ) -> None:
        mock_repo.get_by_account_number.return_value = make_account_doc()
        mock_repo.update.return_value = CLOSED_DOC
        payload = AccountCloseRequest(closure_reason="Closing account now.")
        await account_service.close_account(ACCOUNT_NUMBER, payload, OWNER_ID)
        updates = mock_repo.update.call_args[0][1]
        assert updates["status"] == AccountStatus.CLOSED.value

    @pytest.mark.asyncio
    async def test_close_account_includes_closure_reason_in_updates(
        self, account_service: AccountService, mock_repo: AsyncMock
    ) -> None:
        mock_repo.get_by_account_number.return_value = make_account_doc()
        mock_repo.update.return_value = CLOSED_DOC
        payload = AccountCloseRequest(closure_reason="Switching banks.")
        await account_service.close_account(ACCOUNT_NUMBER, payload, OWNER_ID)
        updates = mock_repo.update.call_args[0][1]
        assert updates["closure_reason"] == "Switching banks."

    @pytest.mark.asyncio
    async def test_close_account_includes_closed_at_in_updates(
        self, account_service: AccountService, mock_repo: AsyncMock
    ) -> None:
        mock_repo.get_by_account_number.return_value = make_account_doc()
        mock_repo.update.return_value = CLOSED_DOC
        payload = AccountCloseRequest(closure_reason="Closing account now.")
        await account_service.close_account(ACCOUNT_NUMBER, payload, OWNER_ID)
        updates = mock_repo.update.call_args[0][1]
        assert updates["closed_at"] is not None

    @pytest.mark.asyncio
    async def test_close_account_not_found_raises_account_not_found(
        self, account_service: AccountService, mock_repo: AsyncMock
    ) -> None:
        mock_repo.get_by_account_number.return_value = None
        with pytest.raises(AccountNotFoundException):
            await account_service.close_account(
                ACCOUNT_NUMBER, AccountCloseRequest(closure_reason="gone."), OWNER_ID
            )

    @pytest.mark.asyncio
    async def test_close_account_wrong_owner_raises_insufficient_permissions(
        self, account_service: AccountService, mock_repo: AsyncMock
    ) -> None:
        mock_repo.get_by_account_number.return_value = make_account_doc(
            owner_id=OTHER_OWNER_ID
        )
        with pytest.raises(InsufficientPermissionsException):
            await account_service.close_account(
                ACCOUNT_NUMBER, AccountCloseRequest(closure_reason="gone."), OWNER_ID
            )

    @pytest.mark.asyncio
    async def test_close_account_already_closed_raises_already_closed(
        self, account_service: AccountService, mock_repo: AsyncMock
    ) -> None:
        closed = make_account_doc(status=AccountStatus.CLOSED.value, is_deleted=False)
        mock_repo.get_by_account_number.return_value = closed
        with pytest.raises(AccountAlreadyClosedException):
            await account_service.close_account(
                ACCOUNT_NUMBER, AccountCloseRequest(closure_reason="gone."), OWNER_ID
            )


class TestAdminListAllAccounts:
    """Tests for AccountService.admin_list_all_accounts()."""

    @pytest.mark.asyncio
    async def test_admin_list_all_calls_list_all_with_include_closed_true(
        self, account_service: AccountService, mock_repo: AsyncMock
    ) -> None:
        mock_repo.list_all.return_value = []
        await account_service.admin_list_all_accounts(include_closed=True)
        mock_repo.list_all.assert_called_once_with(include_closed=True)

    @pytest.mark.asyncio
    async def test_admin_list_all_calls_list_all_with_include_closed_false(
        self, account_service: AccountService, mock_repo: AsyncMock
    ) -> None:
        mock_repo.list_all.return_value = []
        await account_service.admin_list_all_accounts(include_closed=False)
        mock_repo.list_all.assert_called_once_with(include_closed=False)

    @pytest.mark.asyncio
    async def test_admin_list_all_returns_list_of_admin_responses(
        self, account_service: AccountService, mock_repo: AsyncMock
    ) -> None:
        mock_repo.list_all.return_value = [make_account_doc(), CLOSED_DOC]
        result = await account_service.admin_list_all_accounts()
        assert len(result) == 2
        assert all(isinstance(a, AccountAdminResponse) for a in result)


class TestAdminGetAccount:
    """Tests for AccountService.admin_get_account()."""

    @pytest.mark.asyncio
    async def test_admin_get_account_success_returns_admin_response(
        self, account_service: AccountService, mock_repo: AsyncMock
    ) -> None:
        mock_repo.get_by_account_number.return_value = CLOSED_DOC
        result = await account_service.admin_get_account(ACCOUNT_NUMBER)
        assert isinstance(result, AccountAdminResponse)

    @pytest.mark.asyncio
    async def test_admin_get_account_closed_account_does_not_raise(
        self, account_service: AccountService, mock_repo: AsyncMock
    ) -> None:
        mock_repo.get_by_account_number.return_value = CLOSED_DOC
        result = await account_service.admin_get_account(ACCOUNT_NUMBER)
        assert result.is_deleted is True

    @pytest.mark.asyncio
    async def test_admin_get_account_none_raises_account_not_found(
        self, account_service: AccountService, mock_repo: AsyncMock
    ) -> None:
        mock_repo.get_by_account_number.return_value = None
        with pytest.raises(AccountNotFoundException):
            await account_service.admin_get_account(ACCOUNT_NUMBER)


class TestGetBalanceByType:
    """Tests for AccountService.get_balance_by_type()."""

    @pytest.mark.asyncio
    async def test_get_balance_by_type_success_returns_balance_response(
        self, account_service: AccountService, mock_repo: AsyncMock
    ) -> None:
        mock_repo.list_by_owner.return_value = [make_account_doc()]
        result = await account_service.get_balance_by_type(
            AccountType.SAVINGS, OWNER_ID
        )
        assert isinstance(result, AccountBalanceResponse)

    @pytest.mark.asyncio
    async def test_get_balance_by_type_success_returns_decimal_balance(
        self, account_service: AccountService, mock_repo: AsyncMock
    ) -> None:
        mock_repo.list_by_owner.return_value = [make_account_doc()]
        result = await account_service.get_balance_by_type(
            AccountType.SAVINGS, OWNER_ID
        )
        assert result.available_balance == Decimal("500.00")

    @pytest.mark.asyncio
    async def test_get_balance_by_type_not_found_raises_account_type_not_found(
        self, account_service: AccountService, mock_repo: AsyncMock
    ) -> None:
        mock_repo.list_by_owner.return_value = []
        with pytest.raises(AccountTypeNotFoundException):
            await account_service.get_balance_by_type(AccountType.CURRENT, OWNER_ID)

    @pytest.mark.asyncio
    async def test_get_balance_by_type_calls_list_by_owner_with_include_closed_false(
        self, account_service: AccountService, mock_repo: AsyncMock
    ) -> None:
        mock_repo.list_by_owner.return_value = [make_account_doc()]
        await account_service.get_balance_by_type(AccountType.SAVINGS, OWNER_ID)
        mock_repo.list_by_owner.assert_called_once_with(OWNER_ID, include_closed=False)

    @pytest.mark.asyncio
    async def test_get_balance_by_type_selects_most_recent_matching_account(
        self, account_service: AccountService, mock_repo: AsyncMock
    ) -> None:
        older = make_account_doc(account_number="1111111111")
        older["updated_at"] = "2026-03-01T00:00:00+00:00"

        newer = make_account_doc(account_number="2222222222")
        newer["updated_at"] = "2026-03-10T00:00:00+00:00"

        current = make_account_doc(account_number="3333333333")
        current["account_type"] = AccountType.CURRENT.value

        mock_repo.list_by_owner.return_value = [older, current, newer]

        result = await account_service.get_balance_by_type(
            AccountType.SAVINGS, OWNER_ID
        )
        assert result.account_number == "2222222222"
