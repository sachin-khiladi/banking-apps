"""Unit tests for src/services/user_profile_service.py.

All repository interactions are provided via AsyncMock.
No real Cosmos DB connections are made.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from src.exceptions.domain_exceptions import UserProfileNotFoundException
from src.models.user_profile import (
    Address,
    UserProfileResponse,
    UserProfileUpdateRequest,
)
from src.services.user_profile_service import UserProfileService

# ── Constants ──────────────────────────────────────────────────────────────────

OWNER_ID = "user-abc-123"
NOW_ISO = "2026-03-19T10:00:00+00:00"

PROFILE_DOC: dict = {
    "owner_id": OWNER_ID,
    "email": "jane.doe@example.com",
    "mobile_no": "+12065550100",
    "address": {
        "line1": "123 Main Street",
        "line2": "Apt 4B",
        "city": "Seattle",
        "state": "WA",
        "postal_code": "98101",
        "country": "US",
    },
    "created_at": NOW_ISO,
    "updated_at": NOW_ISO,
}


# ── Fixtures ───────────────────────────────────────────────────────────────────


@pytest.fixture
def mock_profile_repo() -> AsyncMock:
    """Provide a fully-mocked IUserProfileRepository with sensible defaults."""
    repo = AsyncMock()
    repo.get_by_owner_id.return_value = PROFILE_DOC
    repo.upsert.return_value = PROFILE_DOC
    return repo


@pytest.fixture
def profile_service(mock_profile_repo: AsyncMock) -> UserProfileService:
    """Provide UserProfileService backed by the mock repository."""
    return UserProfileService(repository=mock_profile_repo)


# ── get_profile ────────────────────────────────────────────────────────────────


class TestGetProfile:
    """Tests for UserProfileService.get_profile()."""

    @pytest.mark.asyncio
    async def test_get_profile_calls_repo_get_by_owner_id(
        self, profile_service: UserProfileService, mock_profile_repo: AsyncMock
    ) -> None:
        await profile_service.get_profile(OWNER_ID)
        mock_profile_repo.get_by_owner_id.assert_called_once_with(OWNER_ID)

    @pytest.mark.asyncio
    async def test_get_profile_returns_user_profile_response(
        self, profile_service: UserProfileService
    ) -> None:
        result = await profile_service.get_profile(OWNER_ID)
        assert isinstance(result, UserProfileResponse)

    @pytest.mark.asyncio
    async def test_get_profile_response_owner_id_matches(
        self, profile_service: UserProfileService
    ) -> None:
        result = await profile_service.get_profile(OWNER_ID)
        assert result.owner_id == OWNER_ID

    @pytest.mark.asyncio
    async def test_get_profile_response_email_matches(
        self, profile_service: UserProfileService
    ) -> None:
        result = await profile_service.get_profile(OWNER_ID)
        assert str(result.email) == "jane.doe@example.com"

    @pytest.mark.asyncio
    async def test_get_profile_raises_not_found_when_repo_returns_none(
        self, profile_service: UserProfileService, mock_profile_repo: AsyncMock
    ) -> None:
        mock_profile_repo.get_by_owner_id.return_value = None
        with pytest.raises(UserProfileNotFoundException):
            await profile_service.get_profile(OWNER_ID)

    @pytest.mark.asyncio
    async def test_get_profile_not_found_exception_carries_owner_id(
        self, profile_service: UserProfileService, mock_profile_repo: AsyncMock
    ) -> None:
        mock_profile_repo.get_by_owner_id.return_value = None
        with pytest.raises(UserProfileNotFoundException) as exc_info:
            await profile_service.get_profile(OWNER_ID)
        assert exc_info.value.owner_id == OWNER_ID


# ── update_profile ─────────────────────────────────────────────────────────────


class TestUpdateProfile:
    """Tests for UserProfileService.update_profile()."""

    @pytest.mark.asyncio
    async def test_update_profile_returns_user_profile_response(
        self, profile_service: UserProfileService
    ) -> None:
        payload = UserProfileUpdateRequest(email="new@example.com")
        result = await profile_service.update_profile(OWNER_ID, payload)
        assert isinstance(result, UserProfileResponse)

    @pytest.mark.asyncio
    async def test_update_profile_calls_repo_upsert(
        self, profile_service: UserProfileService, mock_profile_repo: AsyncMock
    ) -> None:
        payload = UserProfileUpdateRequest(mobile_no="+442071234567")
        await profile_service.update_profile(OWNER_ID, payload)
        mock_profile_repo.upsert.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_profile_creates_new_when_no_existing(
        self, profile_service: UserProfileService, mock_profile_repo: AsyncMock
    ) -> None:
        """When repo returns None the service must still call upsert (create path)."""
        mock_profile_repo.get_by_owner_id.return_value = None
        # Set upsert to return a valid full doc so Pydantic validation passes
        mock_profile_repo.upsert.return_value = PROFILE_DOC
        payload = UserProfileUpdateRequest(
            email="new@example.com", mobile_no="+12065550100"
        )
        await profile_service.update_profile(OWNER_ID, payload)
        mock_profile_repo.upsert.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_profile_new_doc_contains_owner_id(
        self, profile_service: UserProfileService, mock_profile_repo: AsyncMock
    ) -> None:
        mock_profile_repo.get_by_owner_id.return_value = None
        mock_profile_repo.upsert.return_value = PROFILE_DOC
        payload = UserProfileUpdateRequest(
            email="new@example.com", mobile_no="+12065550100"
        )
        await profile_service.update_profile(OWNER_ID, payload)
        upserted_doc = mock_profile_repo.upsert.call_args[0][0]
        assert upserted_doc["owner_id"] == OWNER_ID

    @pytest.mark.asyncio
    async def test_update_profile_merges_email_into_existing_doc(
        self, profile_service: UserProfileService, mock_profile_repo: AsyncMock
    ) -> None:
        mock_profile_repo.upsert.return_value = {
            **PROFILE_DOC,
            "email": "new@example.com",
        }
        payload = UserProfileUpdateRequest(email="new@example.com")
        await profile_service.update_profile(OWNER_ID, payload)
        upserted_doc = mock_profile_repo.upsert.call_args[0][0]
        assert upserted_doc["email"] == "new@example.com"

    @pytest.mark.asyncio
    async def test_update_profile_does_not_overwrite_email_when_not_supplied(
        self, profile_service: UserProfileService, mock_profile_repo: AsyncMock
    ) -> None:
        """Omitting email in the payload must leave the existing email intact."""
        payload = UserProfileUpdateRequest(mobile_no="+442071234567")
        await profile_service.update_profile(OWNER_ID, payload)
        upserted_doc = mock_profile_repo.upsert.call_args[0][0]
        assert upserted_doc["email"] == PROFILE_DOC["email"]

    @pytest.mark.asyncio
    async def test_update_profile_merges_partial_address_without_clobbering(
        self, profile_service: UserProfileService, mock_profile_repo: AsyncMock
    ) -> None:
        """Supplying only line1 must preserve city/state/postal_code from existing."""
        mock_profile_repo.upsert.return_value = PROFILE_DOC
        payload = UserProfileUpdateRequest(
            address=Address(
                line1="999 New Road",
                city="Seattle",
                state="WA",
                postal_code="98101",
                country="US",
            )
        )
        await profile_service.update_profile(OWNER_ID, payload)
        upserted_doc = mock_profile_repo.upsert.call_args[0][0]
        # The new line1 should be set
        assert upserted_doc["address"]["line1"] == "999 New Road"
        # pre-existing city must survive the merge
        assert upserted_doc["address"]["city"] == "Seattle"

    @pytest.mark.asyncio
    async def test_update_profile_overwrites_mobile_no_field(
        self, profile_service: UserProfileService, mock_profile_repo: AsyncMock
    ) -> None:
        new_mobile = "+442071234567"
        mock_profile_repo.upsert.return_value = {**PROFILE_DOC, "mobile_no": new_mobile}
        payload = UserProfileUpdateRequest(mobile_no=new_mobile)
        await profile_service.update_profile(OWNER_ID, payload)
        upserted_doc = mock_profile_repo.upsert.call_args[0][0]
        assert upserted_doc["mobile_no"] == new_mobile

    @pytest.mark.asyncio
    async def test_update_profile_owner_id_always_authoritative(
        self, profile_service: UserProfileService, mock_profile_repo: AsyncMock
    ) -> None:
        """owner_id in the persisted doc must always equal the argument not any field."""
        payload = UserProfileUpdateRequest(email="test@example.com")
        await profile_service.update_profile(OWNER_ID, payload)
        upserted_doc = mock_profile_repo.upsert.call_args[0][0]
        assert upserted_doc["owner_id"] == OWNER_ID

    @pytest.mark.asyncio
    async def test_update_profile_skips_address_when_not_supplied(
        self, profile_service: UserProfileService, mock_profile_repo: AsyncMock
    ) -> None:
        """Omitting address must preserve the existing address dict."""
        payload = UserProfileUpdateRequest(email="test@example.com")
        await profile_service.update_profile(OWNER_ID, payload)
        upserted_doc = mock_profile_repo.upsert.call_args[0][0]
        assert upserted_doc["address"] == PROFILE_DOC["address"]
