"""Cosmos DB implementation of IUserProfileRepository.

Uses azure-cosmos async SDK with DefaultAzureCredential (managed identity).
All Cosmos SDK exceptions are caught at this boundary and re-raised as
RepositoryException so the service layer never sees SDK-specific errors.

Environment variables required:
  COSMOS_ACCOUNT_URL  — e.g. https://<account>.documents.azure.com:443/
  COSMOS_DB_NAME      — the Cosmos DB database name
"""

from __future__ import annotations

import os
from typing import Optional

from azure.cosmos.aio import CosmosClient
from azure.cosmos.exceptions import CosmosHttpResponseError, CosmosResourceNotFoundError
from azure.identity.aio import DefaultAzureCredential
from opentelemetry import trace

from src.exceptions.domain_exceptions import RepositoryException
from src.repository.interfaces.i_user_profile_repository import IUserProfileRepository

tracer = trace.get_tracer(__name__)

_CONTAINER_NAME = "user_profiles"
_PARTITION_KEY = "owner_id"


class CosmosUserProfileRepository(IUserProfileRepository):
    """Async Cosmos DB implementation of IUserProfileRepository.

    Connects via DefaultAzureCredential — no connection strings or
    embedded secrets.  Each public method opens a short-lived CosmosClient
    to stay compatible with Azure Container Apps managed identity lifecycle.

    Attributes:
        _account_url: Cosmos DB account endpoint from env var COSMOS_ACCOUNT_URL.
        _database_name: Database name from env var COSMOS_DB_NAME.
    """

    def __init__(self) -> None:
        """Read connection configuration from environment variables.

        Raises:
            RepositoryException: If required environment variables are missing.
        """
        self._account_url = os.environ.get("COSMOS_ACCOUNT_URL", "")
        self._database_name = os.environ.get("COSMOS_DB_NAME", "")
        if not self._account_url or not self._database_name:
            raise RepositoryException(
                "COSMOS_ACCOUNT_URL and COSMOS_DB_NAME environment variables must be set."
            )

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _new_client(self) -> CosmosClient:
        """Create a new async CosmosClient using DefaultAzureCredential.

        Returns:
            An unauthenticated CosmosClient; authentication is deferred
            until the first network request.
        """
        credential = DefaultAzureCredential()
        return CosmosClient(self._account_url, credential=credential)

    @staticmethod
    def _doc_to_dict(item: dict) -> dict:
        """Normalise a Cosmos DB item to the application's flat dict schema.

        Strips internal Cosmos metadata fields (_rid, _self, _etag, etc.)
        and returns only application-level fields.

        Args:
            item: Raw Cosmos DB item dict.

        Returns:
            Normalised dict ready for Pydantic model construction.
        """
        return {
            "owner_id": item.get("owner_id"),
            "email": item.get("email"),
            "mobile_no": item.get("mobile_no"),
            "address": item.get("address"),
            "created_at": item.get("created_at"),
            "updated_at": item.get("updated_at"),
        }

    @staticmethod
    def _to_cosmos_doc(document: dict) -> dict:
        """Convert application dict to a Cosmos DB document.

        Uses owner_id as the Cosmos document 'id' (doubles as partition key).

        Args:
            document: Application-layer profile dict.

        Returns:
            Cosmos-ready dict with 'id' field set to owner_id.
        """
        return {
            "id": document["owner_id"],
            "owner_id": document["owner_id"],
            "email": document.get("email"),
            "mobile_no": document.get("mobile_no"),
            "address": document.get("address"),
            "created_at": document.get("created_at"),
            "updated_at": document.get("updated_at"),
        }

    # ── IUserProfileRepository implementation ─────────────────────────────────

    async def get_by_owner_id(self, owner_id: str) -> Optional[dict]:
        """Retrieve a user profile document by owner_id from Cosmos DB.

        Args:
            owner_id: The JWT sub of the profile owner (document id + partition key).

        Returns:
            Normalised profile dict, or None if no document exists.

        Raises:
            RepositoryException: On Cosmos DB read failure (excluding 404).
        """
        with tracer.start_as_current_span("CosmosUserProfileRepository.get_by_owner_id") as span:
            span.set_attribute("owner_id", owner_id)
            try:
                async with self._new_client() as client:
                    container = client.get_database_client(
                        self._database_name
                    ).get_container_client(_CONTAINER_NAME)
                    item = await container.read_item(item=owner_id, partition_key=owner_id)
                    return self._doc_to_dict(item)
            except CosmosResourceNotFoundError:
                return None
            except CosmosHttpResponseError as exc:
                raise RepositoryException(
                    f"Failed to retrieve profile for owner {owner_id}: {exc.message}",
                    cause=exc,
                ) from exc

    async def upsert(self, document: dict) -> dict:
        """Create or replace a user profile document in Cosmos DB.

        Args:
            document: Application-layer profile dict containing owner_id.

        Returns:
            Normalised profile dict as persisted in Cosmos DB.

        Raises:
            RepositoryException: On Cosmos DB write failure.
        """
        with tracer.start_as_current_span("CosmosUserProfileRepository.upsert") as span:
            span.set_attribute("owner_id", document.get("owner_id", ""))
            cosmos_doc = self._to_cosmos_doc(document)
            try:
                async with self._new_client() as client:
                    container = client.get_database_client(
                        self._database_name
                    ).get_container_client(_CONTAINER_NAME)
                    saved = await container.upsert_item(body=cosmos_doc)
                    return self._doc_to_dict(saved)
            except CosmosHttpResponseError as exc:
                raise RepositoryException(
                    f"Failed to upsert profile for owner {document.get('owner_id')}: {exc.message}",
                    cause=exc,
                ) from exc
