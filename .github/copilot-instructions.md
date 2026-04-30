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

# GitHub Actions workflow YAML validation (run whenever .github/workflows/*.yml changes)
# 1. Permission-scope check — rejects unknown scopes (e.g. 'variables: write') that
#    cause GitHub to abort the entire workflow before any job runs.
python3 - <<'EOF'
import yaml, sys, pathlib
VALID_PERMISSIONS = {
    "actions","checks","contents","deployments","discussions",
    "id-token","issues","packages","pages","pull-requests",
    "repository-projects","security-events","statuses","workflows"
}
errors = []
for f in sorted(pathlib.Path(".github/workflows").glob("*.yml")):
    try:
        doc = yaml.safe_load(f.read_text())
        for scope_dict in [
            doc.get("permissions", {}),
            *[j.get("permissions", {}) for j in (doc.get("jobs") or {}).values()]
        ]:
            if isinstance(scope_dict, dict):
                bad = set(scope_dict) - VALID_PERMISSIONS
                if bad: errors.append(f"{f}: invalid permission scope(s): {sorted(bad)}")
    except yaml.YAMLError as e:
        errors.append(f"{f}: YAML error: {e}")
if errors:
    [print(e) for e in errors]; sys.exit(1)
print("Workflow YAML permission scopes: OK")
EOF

# 2. SHA tag consistency — build workflow is the ACR tag source of truth;
#    cd.yml must use the same truncation length to avoid MANIFEST_UNKNOWN.
BUILD_LEN=$(grep -oP 'GITHUB_SHA:0:\K\d+' .github/workflows/workflow-build-v1.0.0.yml 2>/dev/null | head -1)
CD_LEN=$(grep -oP 'SHORT_SHA:0:\K\d+' .github/workflows/cd.yml 2>/dev/null | head -1)
[ "$BUILD_LEN" = "$CD_LEN" ] && echo "SHA truncation consistent (${BUILD_LEN} chars): OK" \
  || { echo "SHA mismatch: build=${BUILD_LEN}, cd=${CD_LEN}"; exit 1; }
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
7. **Infra-First Deploy Orchestration**: For GitHub Actions, infrastructure apply workflows must complete successfully before any app deployment workflow runs. Enforce this through top-level `workflow_run` dependencies (for example, CD depends on infra apply workflows), not direct CI-to-CD deployment triggering.
8. **GitHub Actions YAML Correctness** (`infra-devops-agent` mandatory gate): Whenever a `.github/workflows/*.yml` file is created or modified, run the workflow YAML validation script (see Build & Validation Commands) before concluding the task. Two checks are required: (a) permission-scope validation — GitHub silently rejects unknown scope keys (e.g. `variables: write`) and aborts the whole workflow; valid scopes are `actions`, `checks`, `contents`, `deployments`, `discussions`, `id-token`, `issues`, `packages`, `pages`, `pull-requests`, `repository-projects`, `security-events`, `statuses`, `workflows`; (b) SHA truncation consistency — the image tag length in `cd.yml` must match `workflow-build-v1.0.0.yml` or deployment will fail with `MANIFEST_UNKNOWN`.

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
