"""Unit tests for src/repository/cosmos_user_profile_repository.py.

Mocks all CosmosClient and DefaultAzureCredential interactions; no real
Azure services are contacted.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from azure.cosmos.exceptions import CosmosHttpResponseError, CosmosResourceNotFoundError

from src.exceptions.domain_exceptions import RepositoryException
from src.repository.cosmos_user_profile_repository import CosmosUserProfileRepository

# ── Test data ──────────────────────────────────────────────────────────────────

OWNER_ID = "user-abc-123"
NOW_ISO = "2026-03-19T10:00:00+00:00"

_APP_DOC: dict = {
    "owner_id": OWNER_ID,
    "email": "jane.doe@example.com",
    "mobile_no": "+12065550100",
    "address": {
        "line1": "123 Main Street",
        "city": "Seattle",
        "state": "WA",
        "postal_code": "98101",
        "country": "US",
    },
    "created_at": NOW_ISO,
    "updated_at": NOW_ISO,
}

# Simulates what Cosmos DB returns (includes _rid, _etag noise)
_COSMOS_ITEM: dict = {
    "id": OWNER_ID,
    "owner_id": OWNER_ID,
    "email": "jane.doe@example.com",
    "mobile_no": "+12065550100",
    "address": {
        "line1": "123 Main Street",
        "city": "Seattle",
        "state": "WA",
        "postal_code": "98101",
        "country": "US",
    },
    "created_at": NOW_ISO,
    "updated_at": NOW_ISO,
    "_rid": "abc123",
    "_etag": '"etag-value"',
    "_ts": 1700000000,
}


# ── Helpers ────────────────────────────────────────────────────────────────────


def _make_mock_client(mock_container: MagicMock) -> MagicMock:
    """Build an async-context-manager CosmosClient mock pointing to mock_container."""
    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.get_database_client.return_value.get_container_client.return_value = (
        mock_container
    )
    return mock_client


# ── Fixtures ───────────────────────────────────────────────────────────────────


@pytest.fixture
def repo(monkeypatch: pytest.MonkeyPatch) -> CosmosUserProfileRepository:
    """Provide a CosmosUserProfileRepository with env vars set."""
    monkeypatch.setenv("COSMOS_ACCOUNT_URL", "https://test.documents.azure.com/")
    monkeypatch.setenv("COSMOS_DB_NAME", "test_db")
    return CosmosUserProfileRepository()


# ── __init__ env-var guard ─────────────────────────────────────────────────────


class TestCosmosUserProfileRepositoryInit:
    """Tests for CosmosUserProfileRepository.__init__()."""

    def test_init_raises_when_account_url_missing(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("COSMOS_ACCOUNT_URL", raising=False)
        monkeypatch.setenv("COSMOS_DB_NAME", "my_db")
        with pytest.raises(RepositoryException):
            CosmosUserProfileRepository()

    def test_init_raises_when_db_name_missing(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("COSMOS_ACCOUNT_URL", "https://test.documents.azure.com/")
        monkeypatch.delenv("COSMOS_DB_NAME", raising=False)
        with pytest.raises(RepositoryException):
            CosmosUserProfileRepository()

    def test_init_succeeds_with_both_env_vars(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("COSMOS_ACCOUNT_URL", "https://test.documents.azure.com/")
        monkeypatch.setenv("COSMOS_DB_NAME", "my_db")
        repo = CosmosUserProfileRepository()
        assert repo._account_url == "https://test.documents.azure.com/"
        assert repo._database_name == "my_db"

    def test_init_stores_database_name(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("COSMOS_ACCOUNT_URL", "https://test.documents.azure.com/")
        monkeypatch.setenv("COSMOS_DB_NAME", "banking_db")
        repo = CosmosUserProfileRepository()
        assert repo._database_name == "banking_db"


# ── _doc_to_dict ──────────────────────────────────────────────────────────────


class TestDocToDict:
    """Tests for CosmosUserProfileRepository._doc_to_dict()."""

    def test_doc_to_dict_returns_owner_id(self) -> None:
        result = CosmosUserProfileRepository._doc_to_dict(_COSMOS_ITEM)
        assert result["owner_id"] == OWNER_ID

    def test_doc_to_dict_returns_email(self) -> None:
        result = CosmosUserProfileRepository._doc_to_dict(_COSMOS_ITEM)
        assert result["email"] == "jane.doe@example.com"

    def test_doc_to_dict_returns_mobile_no(self) -> None:
        result = CosmosUserProfileRepository._doc_to_dict(_COSMOS_ITEM)
        assert result["mobile_no"] == "+12065550100"

    def test_doc_to_dict_strips_cosmos_metadata(self) -> None:
        result = CosmosUserProfileRepository._doc_to_dict(_COSMOS_ITEM)
        assert "_rid" not in result
        assert "_etag" not in result
        assert "_ts" not in result

    def test_doc_to_dict_returns_address(self) -> None:
        result = CosmosUserProfileRepository._doc_to_dict(_COSMOS_ITEM)
        assert result["address"]["city"] == "Seattle"


# ── _to_cosmos_doc ─────────────────────────────────────────────────────────────


class TestToCosmosDoc:
    """Tests for CosmosUserProfileRepository._to_cosmos_doc()."""

    def test_to_cosmos_doc_sets_id_to_owner_id(self) -> None:
        result = CosmosUserProfileRepository._to_cosmos_doc(_APP_DOC)
        assert result["id"] == OWNER_ID

    def test_to_cosmos_doc_preserves_owner_id(self) -> None:
        result = CosmosUserProfileRepository._to_cosmos_doc(_APP_DOC)
        assert result["owner_id"] == OWNER_ID

    def test_to_cosmos_doc_preserves_email(self) -> None:
        result = CosmosUserProfileRepository._to_cosmos_doc(_APP_DOC)
        assert result["email"] == _APP_DOC["email"]

    def test_to_cosmos_doc_preserves_mobile_no(self) -> None:
        result = CosmosUserProfileRepository._to_cosmos_doc(_APP_DOC)
        assert result["mobile_no"] == _APP_DOC["mobile_no"]


# ── _new_client ───────────────────────────────────────────────────────────────


class TestNewClient:
    """Tests for CosmosUserProfileRepository._new_client()."""

    def test_new_client_returns_cosmos_client(
        self, repo: CosmosUserProfileRepository
    ) -> None:
        with (
            patch(
                "src.repository.cosmos_user_profile_repository.DefaultAzureCredential"
            ),
            patch(
                "src.repository.cosmos_user_profile_repository.CosmosClient"
            ) as mock_cls,
        ):
            mock_cls.return_value = MagicMock()
            repo._new_client()
            mock_cls.assert_called_once()


# ── get_by_owner_id ───────────────────────────────────────────────────────────


class TestGetByOwnerId:
    """Tests for CosmosUserProfileRepository.get_by_owner_id()."""

    @pytest.mark.asyncio
    async def test_get_by_owner_id_returns_dict_when_found(
        self, repo: CosmosUserProfileRepository
    ) -> None:
        mock_container = MagicMock()
        mock_container.read_item = AsyncMock(return_value=_COSMOS_ITEM)
        mock_client = _make_mock_client(mock_container)

        with patch(
            "src.repository.cosmos_user_profile_repository.CosmosUserProfileRepository._new_client",
            return_value=mock_client,
        ):
            result = await repo.get_by_owner_id(OWNER_ID)

        assert result is not None
        assert result["owner_id"] == OWNER_ID

    @pytest.mark.asyncio
    async def test_get_by_owner_id_calls_read_item_with_owner_id(
        self, repo: CosmosUserProfileRepository
    ) -> None:
        mock_container = MagicMock()
        mock_container.read_item = AsyncMock(return_value=_COSMOS_ITEM)
        mock_client = _make_mock_client(mock_container)

        with patch(
            "src.repository.cosmos_user_profile_repository.CosmosUserProfileRepository._new_client",
            return_value=mock_client,
        ):
            await repo.get_by_owner_id(OWNER_ID)

        mock_container.read_item.assert_called_once_with(
            item=OWNER_ID, partition_key=OWNER_ID
        )

    @pytest.mark.asyncio
    async def test_get_by_owner_id_returns_none_when_not_found(
        self, repo: CosmosUserProfileRepository
    ) -> None:
        mock_container = MagicMock()
        mock_container.read_item = AsyncMock(
            side_effect=CosmosResourceNotFoundError(404, "Not found")
        )
        mock_client = _make_mock_client(mock_container)

        with patch(
            "src.repository.cosmos_user_profile_repository.CosmosUserProfileRepository._new_client",
            return_value=mock_client,
        ):
            result = await repo.get_by_owner_id(OWNER_ID)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_owner_id_raises_repository_exception_on_cosmos_error(
        self, repo: CosmosUserProfileRepository
    ) -> None:
        cosmos_exc = CosmosHttpResponseError(status_code=500, message="Internal error")
        mock_container = MagicMock()
        mock_container.read_item = AsyncMock(side_effect=cosmos_exc)
        mock_client = _make_mock_client(mock_container)

        with patch(
            "src.repository.cosmos_user_profile_repository.CosmosUserProfileRepository._new_client",
            return_value=mock_client,
        ):
            with pytest.raises(RepositoryException):
                await repo.get_by_owner_id(OWNER_ID)


# ── upsert ─────────────────────────────────────────────────────────────────────


class TestUpsert:
    """Tests for CosmosUserProfileRepository.upsert()."""

    @pytest.mark.asyncio
    async def test_upsert_returns_normalised_dict(
        self, repo: CosmosUserProfileRepository
    ) -> None:
        mock_container = MagicMock()
        mock_container.upsert_item = AsyncMock(return_value=_COSMOS_ITEM)
        mock_client = _make_mock_client(mock_container)

        with patch(
            "src.repository.cosmos_user_profile_repository.CosmosUserProfileRepository._new_client",
            return_value=mock_client,
        ):
            result = await repo.upsert(_APP_DOC)

        assert result["owner_id"] == OWNER_ID
        assert "_rid" not in result

    @pytest.mark.asyncio
    async def test_upsert_calls_upsert_item_once(
        self, repo: CosmosUserProfileRepository
    ) -> None:
        mock_container = MagicMock()
        mock_container.upsert_item = AsyncMock(return_value=_COSMOS_ITEM)
        mock_client = _make_mock_client(mock_container)

        with patch(
            "src.repository.cosmos_user_profile_repository.CosmosUserProfileRepository._new_client",
            return_value=mock_client,
        ):
            await repo.upsert(_APP_DOC)

        mock_container.upsert_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_upsert_passes_doc_with_id_field(
        self, repo: CosmosUserProfileRepository
    ) -> None:
        mock_container = MagicMock()
        mock_container.upsert_item = AsyncMock(return_value=_COSMOS_ITEM)
        mock_client = _make_mock_client(mock_container)

        with patch(
            "src.repository.cosmos_user_profile_repository.CosmosUserProfileRepository._new_client",
            return_value=mock_client,
        ):
            await repo.upsert(_APP_DOC)

        call_kwargs = mock_container.upsert_item.call_args
        body = call_kwargs[1].get("body") or call_kwargs[0][0]
        assert body["id"] == OWNER_ID

    @pytest.mark.asyncio
    async def test_upsert_raises_repository_exception_on_cosmos_error(
        self, repo: CosmosUserProfileRepository
    ) -> None:
        cosmos_exc = CosmosHttpResponseError(status_code=500, message="Write error")
        mock_container = MagicMock()
        mock_container.upsert_item = AsyncMock(side_effect=cosmos_exc)
        mock_client = _make_mock_client(mock_container)

        with patch(
            "src.repository.cosmos_user_profile_repository.CosmosUserProfileRepository._new_client",
            return_value=mock_client,
        ):
            with pytest.raises(RepositoryException):
                await repo.upsert(_APP_DOC)

    @pytest.mark.asyncio
    async def test_upsert_existing_document_succeeds(
        self, repo: CosmosUserProfileRepository
    ) -> None:
        """Calling upsert twice should work — second call is an update."""
        updated_item = {**_COSMOS_ITEM, "email": "updated@example.com"}
        mock_container = MagicMock()
        mock_container.upsert_item = AsyncMock(return_value=updated_item)
        mock_client = _make_mock_client(mock_container)

        with patch(
            "src.repository.cosmos_user_profile_repository.CosmosUserProfileRepository._new_client",
            return_value=mock_client,
        ):
            result = await repo.upsert({**_APP_DOC, "email": "updated@example.com"})

        assert result["email"] == "updated@example.com"
