---
applyTo: "src/**/*.py"
---

# Python Source Code Standards

> These instructions apply to every file the agent touches under `src/`.

## Typing & Documentation

- **All** function parameters and return types must be annotated — no bare `Any` without justification
- **Every** module, class, and public function must have a Google-style docstring
- Example:
  ```python
  def get_account(self, account_id: str) -> AccountModel:
      """Retrieve an account by ID.

      Args:
          account_id: The unique account identifier.

      Returns:
          The matching AccountModel.

      Raises:
          AccountNotFoundException: If the account does not exist.
          RepositoryException: On unexpected data-access errors.
      """
  ```

## SOLID Enforcement

- **SRP**: One class = one responsibility. Split if a class handles both HTTP and business logic.
- **DIP**: Service layer depends only on repository *interfaces* (ABCs in `interfaces/`), never concrete classes.
- **OCP**: Extend via new classes/methods, not by modifying existing logic branches.

## Dependency Injection

```python
# CORRECT — use Depends()
async def create_account(
    request: AccountCreateRequest,
    service: AccountService = Depends(get_account_service)
) -> AccountResponse:

# FORBIDDEN — instantiating inside function
async def create_account(request: AccountCreateRequest):
    service = AccountService(CosmosAccountRepository())  # ❌
```

## Exception Handling

```python
# CORRECT — use domain exceptions, add context at each layer
except CosmosHttpResponseError as exc:
    raise RepositoryException(
        message=f"Failed to retrieve account {account_id}",
        cause=exc
    ) from exc

# FORBIDDEN — bare except or generic RuntimeError
except Exception:  # ❌
    raise RuntimeError("Something went wrong")  # ❌
```

## Azure SDK Usage

```python
# CORRECT
from azure.identity.aio import DefaultAzureCredential
credential = DefaultAzureCredential()

# FORBIDDEN
client = CosmosClient(url, credential="my-secret-key")  # ❌
```

## Logging

- Use OpenTelemetry spans for all operations
- Include `user_id`, `request_id`, `operation_name` as span attributes
- Log at `INFO` for normal operations, `ERROR` for exceptions with full context
- Never log PII (account numbers in full, passwords, tokens)
