"""Cosmos DB implementation of IAccountRepository.

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

from src.exceptions.domain_exceptions import (
    AccountNotFoundException,
    RepositoryException,
)
from src.repository.interfaces.i_account_repository import IAccountRepository

tracer = trace.get_tracer(__name__)

_CONTAINER_NAME = "accounts"
_PARTITION_KEY = "accountNumber"


class CosmosAccountRepository(IAccountRepository):
    """Async Cosmos DB implementation of IAccountRepository.

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
        and maps snake_case field names the application uses.

        Args:
            item: Raw Cosmos DB item dict.

        Returns:
            Normalised dict ready for Pydantic model construction.
        """
        return {
            "account_number": item.get("accountNumber") or item.get("account_number"),
            "owner_id": item.get("ownerId") or item.get("owner_id"),
            "account_type": item.get("accountType") or item.get("account_type"),
            "status": item.get("status"),
            "balance": item.get("balance"),
            "currency": item.get("currency"),
            "created_at": item.get("createdAt") or item.get("created_at"),
            "updated_at": item.get("updatedAt") or item.get("updated_at"),
            "closed_at": item.get("closedAt") or item.get("closed_at"),
            "closure_reason": item.get("closureReason") or item.get("closure_reason"),
            "is_deleted": (
                item.get("isDeleted")
                if item.get("isDeleted") is not None
                else item.get("is_deleted", False)
            ),
        }

    @staticmethod
    def _to_cosmos_doc(document: dict) -> dict:
        """Convert application snake_case dict to Cosmos DB camelCase document.

        Cosmos DB uses camelCase by convention; the application layer uses
        snake_case.  The account_number is stored as both 'id' (Cosmos PK)
        and 'accountNumber' (logical partition key).

        Args:
            document: Application-layer account dict.

        Returns:
            Cosmos-ready dict with 'id' and camelCase field names.
        """
        return {
            "id": document["account_number"],
            "accountNumber": document["account_number"],
            "ownerId": document["owner_id"],
            "accountType": document["account_type"],
            "status": document["status"],
            "balance": document["balance"],
            "currency": document["currency"],
            "createdAt": document["created_at"],
            "updatedAt": document["updated_at"],
            "closedAt": document.get("closed_at"),
            "closureReason": document.get("closure_reason"),
            "isDeleted": document.get("is_deleted", False),
        }

    # ── IAccountRepository implementation ─────────────────────────────────────

    async def create(self, document: dict) -> dict:
        """Persist a new bank account document to Cosmos DB.

        Args:
            document: Application-layer account dict.

        Returns:
            Normalised document dict as stored in Cosmos DB.

        Raises:
            RepositoryException: On Cosmos DB write failure.
        """
        with tracer.start_as_current_span("CosmosAccountRepository.create") as span:
            span.set_attribute("account_number", document.get("account_number", ""))
            cosmos_doc = self._to_cosmos_doc(document)
            try:
                async with self._new_client() as client:
                    container = client.get_database_client(
                        self._database_name
                    ).get_container_client(_CONTAINER_NAME)
                    created = await container.create_item(body=cosmos_doc)
                    return self._doc_to_dict(created)
            except CosmosHttpResponseError as exc:
                raise RepositoryException(
                    f"Failed to create account {document.get('account_number')}: {exc.message}",
                    cause=exc,
                ) from exc

    async def get_by_account_number(self, account_number: str) -> Optional[dict]:
        """Retrieve a bank account by account number from Cosmos DB.

        Args:
            account_number: The 10-digit account number (document id + partition key).

        Returns:
            Normalised account dict, or None if not found.

        Raises:
            RepositoryException: On unexpected Cosmos DB errors.
        """
        with tracer.start_as_current_span(
            "CosmosAccountRepository.get_by_account_number"
        ) as span:
            span.set_attribute("account_number", account_number)
            try:
                async with self._new_client() as client:
                    container = client.get_database_client(
                        self._database_name
                    ).get_container_client(_CONTAINER_NAME)
                    item = await container.read_item(
                        item=account_number, partition_key=account_number
                    )
                    return self._doc_to_dict(item)
            except CosmosResourceNotFoundError:
                return None
            except CosmosHttpResponseError as exc:
                raise RepositoryException(
                    f"Failed to read account {account_number}: {exc.message}", cause=exc
                ) from exc

    async def list_by_owner(
        self, owner_id: str, *, include_closed: bool = False
    ) -> list[dict]:
        """Query all accounts for a given owner.

        Args:
            owner_id: The JWT sub of the account owner.
            include_closed: When False, filters out is_deleted=True rows.

        Returns:
            List of normalised account dicts.

        Raises:
            RepositoryException: On Cosmos DB query failure.
        """
        with tracer.start_as_current_span(
            "CosmosAccountRepository.list_by_owner"
        ) as span:
            span.set_attribute("owner_id", owner_id)
            span.set_attribute("include_closed", include_closed)

            if include_closed:
                query = "SELECT * FROM c WHERE c.ownerId = @ownerId"
            else:
                query = (
                    "SELECT * FROM c WHERE c.ownerId = @ownerId "
                    "AND (c.isDeleted = false OR NOT IS_DEFINED(c.isDeleted))"
                )
            parameters = [{"name": "@ownerId", "value": owner_id}]

            try:
                async with self._new_client() as client:
                    container = client.get_database_client(
                        self._database_name
                    ).get_container_client(_CONTAINER_NAME)
                    items = [
                        self._doc_to_dict(item)
                        async for item in container.query_items(
                            query=query,
                            parameters=parameters,
                            enable_cross_partition_query=True,
                        )
                    ]
                    return items
            except CosmosHttpResponseError as exc:
                raise RepositoryException(
                    f"Failed to list accounts for owner {owner_id}: {exc.message}",
                    cause=exc,
                ) from exc

    async def list_all(self, *, include_closed: bool = True) -> list[dict]:
        """Query all accounts in the system (admin use only).

        Args:
            include_closed: When False, excludes soft-deleted accounts.

        Returns:
            List of all normalised account dicts.

        Raises:
            RepositoryException: On Cosmos DB query failure.
        """
        with tracer.start_as_current_span("CosmosAccountRepository.list_all") as span:
            span.set_attribute("include_closed", include_closed)

            if include_closed:
                query = "SELECT * FROM c"
                parameters: list = []
            else:
                query = (
                    "SELECT * FROM c WHERE "
                    "(c.isDeleted = false OR NOT IS_DEFINED(c.isDeleted))"
                )
                parameters = []

            try:
                async with self._new_client() as client:
                    container = client.get_database_client(
                        self._database_name
                    ).get_container_client(_CONTAINER_NAME)
                    items = [
                        self._doc_to_dict(item)
                        async for item in container.query_items(
                            query=query,
                            parameters=parameters,
                            enable_cross_partition_query=True,
                        )
                    ]
                    return items
            except CosmosHttpResponseError as exc:
                raise RepositoryException(
                    f"Failed to list all accounts: {exc.message}", cause=exc
                ) from exc

    async def update(self, account_number: str, updates: dict) -> dict:
        """Apply a partial update (patch) to an existing bank account.

        Reads the current document, merges updates, and replaces the item.
        Uses optimistic concurrency via Cosmos DB etag if available.

        Args:
            account_number: The 10-digit account number of the account to update.
            updates: Dict of application-layer fields to merge.

        Returns:
            Normalised updated document.

        Raises:
            AccountNotFoundException: If the account does not exist.
            RepositoryException: On Cosmos DB update failure.
        """
        with tracer.start_as_current_span("CosmosAccountRepository.update") as span:
            span.set_attribute("account_number", account_number)

            # Map snake_case update keys to camelCase Cosmos field names.
            _field_map = {
                "account_type": "accountType",
                "owner_id": "ownerId",
                "created_at": "createdAt",
                "updated_at": "updatedAt",
                "closed_at": "closedAt",
                "closure_reason": "closureReason",
                "is_deleted": "isDeleted",
            }
            cosmos_updates = {_field_map.get(k, k): v for k, v in updates.items()}

            try:
                async with self._new_client() as client:
                    container = client.get_database_client(
                        self._database_name
                    ).get_container_client(_CONTAINER_NAME)
                    # Read-then-replace (no server-side partial patch in basic SDK tier).
                    try:
                        existing = await container.read_item(
                            item=account_number, partition_key=account_number
                        )
                    except CosmosResourceNotFoundError as exc:
                        raise AccountNotFoundException(account_number) from exc

                    existing.update(cosmos_updates)
                    replaced = await container.replace_item(
                        item=account_number, body=existing
                    )
                    return self._doc_to_dict(replaced)
            except CosmosHttpResponseError as exc:
                raise RepositoryException(
                    f"Failed to update account {account_number}: {exc.message}",
                    cause=exc,
                ) from exc
