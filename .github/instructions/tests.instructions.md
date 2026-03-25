---
applyTo: "tests/**/*.py"
---

# Unit Test Standards

> These instructions apply to every file the agent touches under `tests/`.

## Framework & Tools

- **Runner**: `pytest`
- **Coverage**: `pytest-cov` — minimum **85%** per module (`--cov-fail-under=85`)
- **Async**: `pytest-asyncio` for all coroutines
- **Mocking**: `pytest-mock` / `unittest.mock`
- **HTTP testing**: `httpx.AsyncClient` with FastAPI `TestClient`

## Run Command

```bash
pytest tests/ --cov=src --cov-report=term-missing --cov-fail-under=85
```

## Structure Mirror Rule

Mirror `src/` inside `tests/` — one test file per source module:

```
tests/
├── conftest.py                       # shared fixtures only — no test functions
├── test_health.py
├── test_main.py
├── test_auth/test_oauth2.py
├── test_api/test_<router>.py
├── test_services/test_<service>.py
├── test_repository/test_<repo>.py
└── test_exceptions/test_domain_exceptions.py
```

## Design Patterns

- **AAA** pattern: Arrange / Act / Assert — one per function
- **One assertion per test** where possible
- **Naming**: `test_<function>_<scenario>_<expected_outcome>`
  - Example: `test_create_account_duplicate_id_raises_conflict_exception`
- **No logic in tests**: no conditionals, loops, or branching inside test bodies
- **Isolated**: every test sets up and tears down its own state

## Mocking Rules (mandatory)

```python
# ALWAYS mock Azure SDK clients
@pytest.fixture
def mock_cosmos_client(mocker):
    return mocker.patch("src.repository.cosmos_account_repository.CosmosClient")

# ALWAYS mock DefaultAzureCredential
@pytest.fixture
def mock_credential(mocker):
    return mocker.patch("azure.identity.DefaultAzureCredential")
```

- Never call live Azure endpoints in any test
- Never read real environment variables — use `monkeypatch.setenv`
- Scope fixtures: `function` (default), `module` if setup is expensive

## Coverage Per Layer

| Layer | Required Coverage |
|---|---|
| `api/` | HTTP status codes, response schema, 4xx/5xx, auth enforcement |
| `services/` | Business logic paths, domain exceptions, edge cases |
| `repository/` | SDK call arguments, mapping logic, error handling |
| `auth/` | Token validation success/failure, expired tokens |
| `exceptions/` | Attributes, error codes, message formatting |
| `main.py` | App startup, middleware, route inclusion |
