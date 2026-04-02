# FastAPI Azure Banking App — Repository Contract

> **Loaded every session, every agent. Keep this minimal.
> Domain-specific rules live in path-specific instructions and agent profiles.**

---

## Build & Validation Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Lint (must pass — zero critical errors)
pylint src/

# Unit tests + coverage (must reach ≥ 85%)
pytest tests/ --cov=src --cov-report=term-missing --cov-fail-under=85

# Docker build + security scan
docker build -t bankapi . && trivy image --exit-code 1 --severity HIGH,CRITICAL bankapi
```

## Architecture at a Glance

```
src/
├── main.py           # App init, middleware, route registration
├── api/              # HTTP handlers only — no business logic
├── services/         # Business logic — no HTTP knowledge
├── repository/       # Data access (Cosmos DB async SDK)
│   └── interfaces/   # ABCs — service layer depends ONLY on these
├── models/           # Pydantic schemas / DTOs
├── auth/             # OAuth2 Bearer token validation
├── exceptions/       # Domain exception hierarchy
└── logging/          # OpenTelemetry + Azure Monitor exporter
```

## Non-Negotiable Rules (apply to all agents)

1. **Credentials**: Use `DefaultAzureCredential` only. Never hardcode keys, tokens, or connection strings.
2. **Exceptions**: Raise from `src/exceptions/domain_exceptions.py`. Never expose stack traces in HTTP responses.
3. **Dependency Injection**: Use FastAPI `Depends()` or constructor injection. Never instantiate dependencies inside functions.
4. **Testing**: Mock all Azure SDK clients (`CosmosClient`, `DefaultAzureCredential`). Never call live Azure services in unit tests.
5. **Boundaries**: Agents own specific layers — do not cross ownership lines without explicit handoff.
6. **Terraform Artifacts**: Never commit local Terraform runtime artifacts (`.terraform/`, `terraform.tfstate*`, `tfplan*`, `crash.log`, `*_override.tf*`). Ensure these are covered by `.gitignore` before check-in.

## Layer Ownership

| Layer | Owner Agent |
|---|---|
| `src/api/`, `src/services/`, `src/auth/`, `src/exceptions/`, `src/logging/`, `src/main.py` | `python-coding-agent` |
| `src/repository/`, `src/repository/interfaces/` | `cosmosdb-repo-agent` (invoked by `python-coding-agent`) |
| `tests/` | `unit-test-agent` |
| `infra/` | `infra-devops-agent` (Terraform skill required) |
| Azure diagnostics, logs, remediation | `azure-sre-agent` |
| Multi-agent coordination | `orchestrator-agent` |
| Requirement decomposition | `planning-agent` |

## Agent Communication Protocol

All inter-agent handoffs use versioned JSON files in `agents-communication/handoffs/`.

**Naming convention:** `v{schema_version}__{sender-agent}__to__{receiver-agent}__{task-slug}__run-{NNN}.json`

**Example:** `v1__planner__to__coding__add-transfer-api__run-001.json`

Schemas live in `agents-communication/schemas/`. Every agent **MUST** validate its input against the schema before proceeding and write its output using the correct schema before handing off.
