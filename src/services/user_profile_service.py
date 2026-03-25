"""User profile service — business logic for profile lifecycle.

Encodes all domain rules for retrieving and updating user profiles.
Depends only on IUserProfileRepository (injected) and never imports
the Cosmos SDK directly (Dependency Inversion Principle).
"""

from __future__ import annotations

from datetime import datetime, timezone

from opentelemetry import trace

from src.exceptions.domain_exceptions import UserProfileNotFoundException
from src.models.user_profile import UserProfileResponse, UserProfileUpdateRequest
from src.repository.interfaces.i_user_profile_repository import IUserProfileRepository

tracer = trace.get_tracer(__name__)


class UserProfileService:
    """Business-logic layer for user profile management.

    Responsibilities:
    - Retrieve a profile owned by a specific user.
    - Upsert a profile with PATCH semantics (merge non-None fields only).
    - Enforce that owner_id is always sourced from the JWT sub, never
      from the request payload.

    Attributes:
        _repo: Injected IUserProfileRepository implementation.
    """

    def __init__(self, repository: IUserProfileRepository) -> None:
        """Initialise the service with an injected repository.

        Args:
            repository: Concrete implementation of IUserProfileRepository.
        """
        self._repo = repository

    # ── Public methods ─────────────────────────────────────────────────────────

    async def get_profile(self, owner_id: str) -> UserProfileResponse:
        """Retrieve the user profile for the given owner.

        Args:
            owner_id: JWT sub of the requesting user.

        Returns:
            UserProfileResponse populated from the persisted document.

        Raises:
            UserProfileNotFoundException: When no profile exists for owner_id.
        """
        with tracer.start_as_current_span("UserProfileService.get_profile") as span:
            span.set_attribute("owner_id", owner_id)

            doc = await self._repo.get_by_owner_id(owner_id)
            if doc is None:
                raise UserProfileNotFoundException(owner_id)

            return UserProfileResponse(**doc)

    async def update_profile(
        self,
        owner_id: str,
        payload: UserProfileUpdateRequest,
    ) -> UserProfileResponse:
        """Create or update the user profile with PATCH semantics.

        Fetches the existing document (if any) and merges only the non-None
        fields from *payload*.  Nested Address fields are also merged
        field-by-field so a partial address update does not clobber other
        address fields.  The owner_id is always taken from the argument and
        never from the payload.

        Args:
            owner_id: JWT sub of the requesting user; always authoritative.
            payload: UserProfileUpdateRequest with optional fields to update.

        Returns:
            UserProfileResponse reflecting the merged state.
        """
        with tracer.start_as_current_span("UserProfileService.update_profile") as span:
            span.set_attribute("owner_id", owner_id)

            now = datetime.now(timezone.utc)

            # Fetch existing document or start with a skeleton.
            existing = await self._repo.get_by_owner_id(owner_id)
            if existing is None:
                doc: dict = {
                    "owner_id": owner_id,
                    "email": None,
                    "mobile_no": None,
                    "address": None,
                    "created_at": now.isoformat(),
                    "updated_at": now.isoformat(),
                }
            else:
                doc = dict(existing)
                doc["owner_id"] = owner_id  # always authoritative

            # Merge non-None scalar fields.
            if payload.email is not None:
                doc["email"] = str(payload.email)
            if payload.mobile_no is not None:
                doc["mobile_no"] = payload.mobile_no

            # Merge address field-by-field (partial address update).
            if payload.address is not None:
                existing_address: dict = doc.get("address") or {}
                new_address = payload.address.model_dump(exclude_none=False)
                # Only overwrite fields that are explicitly set in the payload.
                merged_address: dict = {**existing_address}
                for field, value in new_address.items():
                    if value is not None:
                        merged_address[field] = value
                doc["address"] = merged_address

            # Always refresh updated_at; set created_at only when creating.
            doc["updated_at"] = now.isoformat()

            saved = await self._repo.upsert(doc)
            return UserProfileResponse(**saved)
