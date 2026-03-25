"""Unit tests for src/repository/cosmos_account_repository.py.

Only the static/pure methods and __init__ env-var guard are tested here
without network calls.  Async Cosmos SDK methods would require a live
endpoint so they are exercised via the mock_repo fixture at the service layer.
"""

from __future__ import annotations

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.exceptions.domain_exceptions import RepositoryException
from src.repository.cosmos_account_repository import CosmosAccountRepository


# ── Helpers ───────────────────────────────────────────────────────────────────

_BASE_DOC = {
    "account_number": "1234567890",
    "owner_id": "user-abc",
    "account_type": "SAVINGS",
    "status": "ACTIVE",
    "balance": "500.00",
    "currency": "USD",
    "created_at": "2026-01-01T00:00:00+00:00",
    "updated_at": "2026-01-01T00:00:00+00:00",
    "closed_at": None,
    "closure_reason": None,
    "is_deleted": False,
}

_CAMEL_ITEM = {
    "id": "1234567890",
    "accountNumber": "1234567890",
    "ownerId": "user-abc",
    "accountType": "SAVINGS",
    "status": "ACTIVE",
    "balance": "500.00",
    "currency": "USD",
    "createdAt": "2026-01-01T00:00:00+00:00",
    "updatedAt": "2026-01-01T00:00:00+00:00",
    "closedAt": None,
    "closureReason": None,
    "isDeleted": False,
}


# ── __init__ env-var guard ────────────────────────────────────────────────────


class TestCosmosAccountRepositoryInit:
    """Tests for CosmosAccountRepository.__init__()."""

    def test_init_raises_repository_exception_when_url_missing(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("COSMOS_ACCOUNT_URL", raising=False)
        monkeypatch.setenv("COSMOS_DB_NAME", "my_db")
        with pytest.raises(RepositoryException) as exc_info:
            CosmosAccountRepository()
        assert "COSMOS_ACCOUNT_URL" in str(exc_info.value)

    def test_init_raises_repository_exception_when_db_name_missing(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("COSMOS_ACCOUNT_URL", "https://test.documents.azure.com/")
        monkeypatch.delenv("COSMOS_DB_NAME", raising=False)
        with pytest.raises(RepositoryException) as exc_info:
            CosmosAccountRepository()
        assert "COSMOS_DB_NAME" in str(exc_info.value)

    def test_init_succeeds_when_both_env_vars_set(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("COSMOS_ACCOUNT_URL", "https://test.documents.azure.com/")
        monkeypatch.setenv("COSMOS_DB_NAME", "my_db")
        repo = CosmosAccountRepository()
        assert repo._account_url == "https://test.documents.azure.com/"
        assert repo._database_name == "my_db"

    def test_init_stores_account_url(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("COSMOS_ACCOUNT_URL", "https://prod.documents.azure.com/")
        monkeypatch.setenv("COSMOS_DB_NAME", "banking")
        repo = CosmosAccountRepository()
        assert repo._account_url == "https://prod.documents.azure.com/"


# ── _to_cosmos_doc ────────────────────────────────────────────────────────────


class TestToCosmosDoc:
    """Tests for CosmosAccountRepository._to_cosmos_doc()."""

    def test_to_cosmos_doc_sets_id_to_account_number(self) -> None:
        result = CosmosAccountRepository._to_cosmos_doc(_BASE_DOC)
        assert result["id"] == "1234567890"

    def test_to_cosmos_doc_sets_account_number_camel_case(self) -> None:
        result = CosmosAccountRepository._to_cosmos_doc(_BASE_DOC)
        assert result["accountNumber"] == "1234567890"

    def test_to_cosmos_doc_maps_owner_id_to_owner_id_camel(self) -> None:
        result = CosmosAccountRepository._to_cosmos_doc(_BASE_DOC)
        assert result["ownerId"] == "user-abc"

    def test_to_cosmos_doc_maps_account_type_to_camel(self) -> None:
        result = CosmosAccountRepository._to_cosmos_doc(_BASE_DOC)
        assert result["accountType"] == "SAVINGS"

    def test_to_cosmos_doc_maps_created_at_to_camel(self) -> None:
        result = CosmosAccountRepository._to_cosmos_doc(_BASE_DOC)
        assert result["createdAt"] == "2026-01-01T00:00:00+00:00"

    def test_to_cosmos_doc_maps_updated_at_to_camel(self) -> None:
        result = CosmosAccountRepository._to_cosmos_doc(_BASE_DOC)
        assert result["updatedAt"] == "2026-01-01T00:00:00+00:00"

    def test_to_cosmos_doc_maps_is_deleted_to_camel(self) -> None:
        result = CosmosAccountRepository._to_cosmos_doc(_BASE_DOC)
        assert result["isDeleted"] is False

    def test_to_cosmos_doc_maps_closed_at_to_camel(self) -> None:
        doc = {**_BASE_DOC, "closed_at": "2026-06-01T00:00:00+00:00"}
        result = CosmosAccountRepository._to_cosmos_doc(doc)
        assert result["closedAt"] == "2026-06-01T00:00:00+00:00"

    def test_to_cosmos_doc_maps_closure_reason_to_camel(self) -> None:
        doc = {**_BASE_DOC, "closure_reason": "Done."}
        result = CosmosAccountRepository._to_cosmos_doc(doc)
        assert result["closureReason"] == "Done."

    def test_to_cosmos_doc_preserves_balance(self) -> None:
        result = CosmosAccountRepository._to_cosmos_doc(_BASE_DOC)
        assert result["balance"] == "500.00"

    def test_to_cosmos_doc_preserves_currency(self) -> None:
        result = CosmosAccountRepository._to_cosmos_doc(_BASE_DOC)
        assert result["currency"] == "USD"


# ── _doc_to_dict ──────────────────────────────────────────────────────────────


class TestDocToDict:
    """Tests for CosmosAccountRepository._doc_to_dict()."""

    def test_doc_to_dict_maps_account_number_from_camel(self) -> None:
        result = CosmosAccountRepository._doc_to_dict(_CAMEL_ITEM)
        assert result["account_number"] == "1234567890"

    def test_doc_to_dict_maps_owner_id_from_camel(self) -> None:
        result = CosmosAccountRepository._doc_to_dict(_CAMEL_ITEM)
        assert result["owner_id"] == "user-abc"

    def test_doc_to_dict_maps_account_type_from_camel(self) -> None:
        result = CosmosAccountRepository._doc_to_dict(_CAMEL_ITEM)
        assert result["account_type"] == "SAVINGS"

    def test_doc_to_dict_maps_created_at_from_camel(self) -> None:
        result = CosmosAccountRepository._doc_to_dict(_CAMEL_ITEM)
        assert result["created_at"] == "2026-01-01T00:00:00+00:00"

    def test_doc_to_dict_maps_updated_at_from_camel(self) -> None:
        result = CosmosAccountRepository._doc_to_dict(_CAMEL_ITEM)
        assert result["updated_at"] == "2026-01-01T00:00:00+00:00"

    def test_doc_to_dict_maps_is_deleted_from_camel(self) -> None:
        result = CosmosAccountRepository._doc_to_dict(_CAMEL_ITEM)
        assert result["is_deleted"] is False

    def test_doc_to_dict_falls_back_to_snake_case_account_number(self) -> None:
        snake_item = {**_BASE_DOC}
        result = CosmosAccountRepository._doc_to_dict(snake_item)
        assert result["account_number"] == "1234567890"

    def test_doc_to_dict_falls_back_to_snake_case_owner_id(self) -> None:
        snake_item = {**_BASE_DOC}
        result = CosmosAccountRepository._doc_to_dict(snake_item)
        assert result["owner_id"] == "user-abc"

    def test_doc_to_dict_defaults_is_deleted_to_false_when_absent(self) -> None:
        item = {k: v for k, v in _CAMEL_ITEM.items() if k not in ("isDeleted", "is_deleted")}
        result = CosmosAccountRepository._doc_to_dict(item)
        assert result["is_deleted"] is False

    def test_doc_to_dict_maps_closure_reason_from_camel(self) -> None:
        item = {**_CAMEL_ITEM, "closureReason": "Done."}
        result = CosmosAccountRepository._doc_to_dict(item)
        assert result["closure_reason"] == "Done."

    def test_doc_to_dict_maps_closed_at_from_camel(self) -> None:
        item = {**_CAMEL_ITEM, "closedAt": "2026-06-01T00:00:00+00:00"}
        result = CosmosAccountRepository._doc_to_dict(item)
        assert result["closed_at"] == "2026-06-01T00:00:00+00:00"


# ── Async method helpers ──────────────────────────────────────────────────────

def _make_async_iter(items: list):
    """Return an object whose __aiter__ yields items — usable in 'async for'."""

    async def _gen():
        for item in items:
            yield item

    return _gen()


def _make_mock_client(mock_container):
    """Build an async-context-manager CosmosClient mock pointing to mock_container."""
    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.get_database_client.return_value.get_container_client.return_value = mock_container
    return mock_client


@pytest.fixture
def repo_fixture(monkeypatch: pytest.MonkeyPatch) -> CosmosAccountRepository:
    """Provide a CosmosAccountRepository with env vars set."""
    monkeypatch.setenv("COSMOS_ACCOUNT_URL", "https://test.documents.azure.com/")
    monkeypatch.setenv("COSMOS_DB_NAME", "test_db")
    return CosmosAccountRepository()


# ── _new_client ───────────────────────────────────────────────────────────────

class TestNewClient:
    """Tests for CosmosAccountRepository._new_client()."""

    def test_new_client_returns_cosmos_client(
        self, repo_fixture: CosmosAccountRepository
    ) -> None:
        from azure.cosmos.aio import CosmosClient

        with patch("src.repository.cosmos_account_repository.DefaultAzureCredential"), \
             patch("src.repository.cosmos_account_repository.CosmosClient") as mock_cls:
            mock_cls.return_value = MagicMock()
            client = repo_fixture._new_client()
            mock_cls.assert_called_once_with(
                repo_fixture._account_url, credential=mock_cls.call_args[1]["credential"]
            )


# ── create ────────────────────────────────────────────────────────────────────

class TestAsyncCreate:
    """Tests for CosmosAccountRepository.create()."""

    @pytest.mark.asyncio
    async def test_create_returns_normalised_dict(
        self, repo_fixture: CosmosAccountRepository
    ) -> None:
        mock_container = AsyncMock()
        mock_container.create_item.return_value = _CAMEL_ITEM
        mock_client = _make_mock_client(mock_container)

        with patch.object(repo_fixture, "_new_client", return_value=mock_client):
            result = await repo_fixture.create(_BASE_DOC)

        assert result["account_number"] == "1234567890"

    @pytest.mark.asyncio
    async def test_create_calls_create_item_once(
        self, repo_fixture: CosmosAccountRepository
    ) -> None:
        mock_container = AsyncMock()
        mock_container.create_item.return_value = _CAMEL_ITEM
        mock_client = _make_mock_client(mock_container)

        with patch.object(repo_fixture, "_new_client", return_value=mock_client):
            await repo_fixture.create(_BASE_DOC)

        mock_container.create_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_passes_camel_case_document_to_create_item(
        self, repo_fixture: CosmosAccountRepository
    ) -> None:
        mock_container = AsyncMock()
        mock_container.create_item.return_value = _CAMEL_ITEM
        mock_client = _make_mock_client(mock_container)

        with patch.object(repo_fixture, "_new_client", return_value=mock_client):
            await repo_fixture.create(_BASE_DOC)

        body = mock_container.create_item.call_args.kwargs["body"]
        assert body["accountNumber"] == "1234567890"

    @pytest.mark.asyncio
    async def test_create_raises_repository_exception_on_cosmos_error(
        self, repo_fixture: CosmosAccountRepository
    ) -> None:
        from azure.cosmos.exceptions import CosmosHttpResponseError

        mock_container = AsyncMock()
        mock_container.create_item.side_effect = CosmosHttpResponseError()
        mock_client = _make_mock_client(mock_container)

        with patch.object(repo_fixture, "_new_client", return_value=mock_client):
            with pytest.raises(RepositoryException):
                await repo_fixture.create(_BASE_DOC)


# ── get_by_account_number ─────────────────────────────────────────────────────

class TestAsyncGetByAccountNumber:
    """Tests for CosmosAccountRepository.get_by_account_number()."""

    @pytest.mark.asyncio
    async def test_get_by_account_number_returns_dict(
        self, repo_fixture: CosmosAccountRepository
    ) -> None:
        mock_container = AsyncMock()
        mock_container.read_item.return_value = _CAMEL_ITEM
        mock_client = _make_mock_client(mock_container)

        with patch.object(repo_fixture, "_new_client", return_value=mock_client):
            result = await repo_fixture.get_by_account_number("1234567890")

        assert result["account_number"] == "1234567890"

    @pytest.mark.asyncio
    async def test_get_by_account_number_returns_none_when_not_found(
        self, repo_fixture: CosmosAccountRepository
    ) -> None:
        from azure.cosmos.exceptions import CosmosResourceNotFoundError

        mock_container = AsyncMock()
        mock_container.read_item.side_effect = CosmosResourceNotFoundError()
        mock_client = _make_mock_client(mock_container)

        with patch.object(repo_fixture, "_new_client", return_value=mock_client):
            result = await repo_fixture.get_by_account_number("0000000000")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_account_number_calls_read_item_with_partition_key(
        self, repo_fixture: CosmosAccountRepository
    ) -> None:
        mock_container = AsyncMock()
        mock_container.read_item.return_value = _CAMEL_ITEM
        mock_client = _make_mock_client(mock_container)

        with patch.object(repo_fixture, "_new_client", return_value=mock_client):
            await repo_fixture.get_by_account_number("1234567890")

        mock_container.read_item.assert_called_once_with(
            item="1234567890", partition_key="1234567890"
        )

    @pytest.mark.asyncio
    async def test_get_by_account_number_raises_repository_exception_on_cosmos_error(
        self, repo_fixture: CosmosAccountRepository
    ) -> None:
        from azure.cosmos.exceptions import CosmosHttpResponseError

        mock_container = AsyncMock()
        mock_container.read_item.side_effect = CosmosHttpResponseError()
        mock_client = _make_mock_client(mock_container)

        with patch.object(repo_fixture, "_new_client", return_value=mock_client):
            with pytest.raises(RepositoryException):
                await repo_fixture.get_by_account_number("1234567890")


# ── list_by_owner ─────────────────────────────────────────────────────────────

class TestAsyncListByOwner:
    """Tests for CosmosAccountRepository.list_by_owner()."""

    @pytest.mark.asyncio
    async def test_list_by_owner_returns_list_of_dicts(
        self, repo_fixture: CosmosAccountRepository
    ) -> None:
        mock_container = MagicMock()
        mock_container.query_items.return_value = _make_async_iter([_CAMEL_ITEM])
        mock_client = _make_mock_client(mock_container)

        with patch.object(repo_fixture, "_new_client", return_value=mock_client):
            result = await repo_fixture.list_by_owner("user-abc")

        assert len(result) == 1
        assert result[0]["account_number"] == "1234567890"

    @pytest.mark.asyncio
    async def test_list_by_owner_returns_empty_list_when_no_items(
        self, repo_fixture: CosmosAccountRepository
    ) -> None:
        mock_container = MagicMock()
        mock_container.query_items.return_value = _make_async_iter([])
        mock_client = _make_mock_client(mock_container)

        with patch.object(repo_fixture, "_new_client", return_value=mock_client):
            result = await repo_fixture.list_by_owner("user-abc")

        assert result == []

    @pytest.mark.asyncio
    async def test_list_by_owner_include_closed_true_returns_results(
        self, repo_fixture: CosmosAccountRepository
    ) -> None:
        closed_item = {**_CAMEL_ITEM, "isDeleted": True}
        mock_container = MagicMock()
        mock_container.query_items.return_value = _make_async_iter([_CAMEL_ITEM, closed_item])
        mock_client = _make_mock_client(mock_container)

        with patch.object(repo_fixture, "_new_client", return_value=mock_client):
            result = await repo_fixture.list_by_owner("user-abc", include_closed=True)

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_list_by_owner_include_closed_false_applies_is_deleted_filter(
        self, repo_fixture: CosmosAccountRepository
    ) -> None:
        mock_container = MagicMock()
        mock_container.query_items.return_value = _make_async_iter([_CAMEL_ITEM])
        mock_client = _make_mock_client(mock_container)

        with patch.object(repo_fixture, "_new_client", return_value=mock_client):
            await repo_fixture.list_by_owner("user-abc", include_closed=False)

        query = mock_container.query_items.call_args.kwargs["query"]
        assert "c.isDeleted = false" in query

    @pytest.mark.asyncio
    async def test_list_by_owner_include_closed_true_excludes_is_deleted_filter(
        self, repo_fixture: CosmosAccountRepository
    ) -> None:
        mock_container = MagicMock()
        mock_container.query_items.return_value = _make_async_iter([_CAMEL_ITEM])
        mock_client = _make_mock_client(mock_container)

        with patch.object(repo_fixture, "_new_client", return_value=mock_client):
            await repo_fixture.list_by_owner("user-abc", include_closed=True)

        query = mock_container.query_items.call_args.kwargs["query"]
        assert "c.isDeleted = false" not in query

    @pytest.mark.asyncio
    async def test_list_by_owner_raises_repository_exception_on_cosmos_error(
        self, repo_fixture: CosmosAccountRepository
    ) -> None:
        from azure.cosmos.exceptions import CosmosHttpResponseError

        # MagicMock (not AsyncMock) so query_items raises synchronously on call
        mock_container = MagicMock()
        mock_container.query_items.side_effect = CosmosHttpResponseError()
        mock_client = _make_mock_client(mock_container)

        with patch.object(repo_fixture, "_new_client", return_value=mock_client):
            with pytest.raises(RepositoryException):
                await repo_fixture.list_by_owner("user-abc")


# ── list_all ──────────────────────────────────────────────────────────────────

class TestAsyncListAll:
    """Tests for CosmosAccountRepository.list_all()."""

    @pytest.mark.asyncio
    async def test_list_all_returns_list_of_dicts(
        self, repo_fixture: CosmosAccountRepository
    ) -> None:
        closed_item = {**_CAMEL_ITEM, "isDeleted": True}
        mock_container = MagicMock()
        mock_container.query_items.return_value = _make_async_iter([_CAMEL_ITEM, closed_item])
        mock_client = _make_mock_client(mock_container)

        with patch.object(repo_fixture, "_new_client", return_value=mock_client):
            result = await repo_fixture.list_all(include_closed=True)

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_list_all_include_closed_false_returns_results(
        self, repo_fixture: CosmosAccountRepository
    ) -> None:
        mock_container = MagicMock()
        mock_container.query_items.return_value = _make_async_iter([_CAMEL_ITEM])
        mock_client = _make_mock_client(mock_container)

        with patch.object(repo_fixture, "_new_client", return_value=mock_client):
            result = await repo_fixture.list_all(include_closed=False)

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_list_all_raises_repository_exception_on_cosmos_error(
        self, repo_fixture: CosmosAccountRepository
    ) -> None:
        from azure.cosmos.exceptions import CosmosHttpResponseError

        # MagicMock (not AsyncMock) so query_items raises synchronously on call
        mock_container = MagicMock()
        mock_container.query_items.side_effect = CosmosHttpResponseError()
        mock_client = _make_mock_client(mock_container)

        with patch.object(repo_fixture, "_new_client", return_value=mock_client):
            with pytest.raises(RepositoryException):
                await repo_fixture.list_all()


# ── update ────────────────────────────────────────────────────────────────────

class TestAsyncUpdate:
    """Tests for CosmosAccountRepository.update()."""

    @pytest.mark.asyncio
    async def test_update_returns_normalised_dict(
        self, repo_fixture: CosmosAccountRepository
    ) -> None:
        updated_cosmos = {**_CAMEL_ITEM, "currency": "EUR"}
        mock_container = AsyncMock()
        mock_container.read_item.return_value = dict(_CAMEL_ITEM)
        mock_container.replace_item.return_value = updated_cosmos
        mock_client = _make_mock_client(mock_container)

        with patch.object(repo_fixture, "_new_client", return_value=mock_client):
            result = await repo_fixture.update("1234567890", {"currency": "EUR"})

        assert result["account_number"] == "1234567890"

    @pytest.mark.asyncio
    async def test_update_calls_replace_item(
        self, repo_fixture: CosmosAccountRepository
    ) -> None:
        mock_container = AsyncMock()
        mock_container.read_item.return_value = dict(_CAMEL_ITEM)
        mock_container.replace_item.return_value = _CAMEL_ITEM
        mock_client = _make_mock_client(mock_container)

        with patch.object(repo_fixture, "_new_client", return_value=mock_client):
            await repo_fixture.update("1234567890", {"currency": "EUR"})

        mock_container.replace_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_maps_snake_case_updates_to_camel_case_document(
        self, repo_fixture: CosmosAccountRepository
    ) -> None:
        mock_container = AsyncMock()
        mock_container.read_item.return_value = dict(_CAMEL_ITEM)
        mock_container.replace_item.return_value = _CAMEL_ITEM
        mock_client = _make_mock_client(mock_container)

        updates = {
            "closure_reason": "Customer requested.",
            "is_deleted": True,
            "updated_at": "2026-03-20T00:00:00+00:00",
        }

        with patch.object(repo_fixture, "_new_client", return_value=mock_client):
            await repo_fixture.update("1234567890", updates)

        body = mock_container.replace_item.call_args.kwargs["body"]
        assert body["closureReason"] == "Customer requested."

    @pytest.mark.asyncio
    async def test_update_raises_account_not_found_when_missing(
        self, repo_fixture: CosmosAccountRepository
    ) -> None:
        from azure.cosmos.exceptions import CosmosResourceNotFoundError

        from src.exceptions.domain_exceptions import AccountNotFoundException

        mock_container = AsyncMock()
        mock_container.read_item.side_effect = CosmosResourceNotFoundError()
        mock_client = _make_mock_client(mock_container)

        with patch.object(repo_fixture, "_new_client", return_value=mock_client):
            with pytest.raises(AccountNotFoundException):
                await repo_fixture.update("9999999999", {"currency": "USD"})

    @pytest.mark.asyncio
    async def test_update_raises_repository_exception_on_cosmos_error(
        self, repo_fixture: CosmosAccountRepository
    ) -> None:
        from azure.cosmos.exceptions import CosmosHttpResponseError

        mock_container = AsyncMock()
        mock_container.read_item.return_value = dict(_CAMEL_ITEM)
        mock_container.replace_item.side_effect = CosmosHttpResponseError()
        mock_client = _make_mock_client(mock_container)

        with patch.object(repo_fixture, "_new_client", return_value=mock_client):
            with pytest.raises(RepositoryException):
                await repo_fixture.update("1234567890", {"currency": "USD"})
