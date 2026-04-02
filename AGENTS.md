# AGENT.md

# FastAPI Azure App - Agent Instructions

## Project Overview
This repository contains a FastAPI application designed to run on Azure, featuring OAuth 2.0 authentication, Azure Application Insights logging, and a structured approach adhering to SOLID design principles.

## FastAPI Application Structure
- **src/main.py**: Entry point for the FastAPI application. Initializes the app, includes the health check route, and sets up middleware for logging and authentication.
- **src/api/health.py**: Defines the health endpoint, returning a simple health check response.
- **src/auth/oauth2.py**: Manages OAuth 2.0 authentication and authorization, including token generation and validation.
- **src/exceptions/domain_exceptions.py**: Contains domain-specific exceptions, providing context for errors.
- **src/logging/app_insights.py**: Integrates Azure Application Insights using OpenTelemetry for logging.
- **src/repository/__init__.py**: Initializes the repository package for data access interfaces and implementations.
- **src/services/__init__.py**: Initializes the services package for business logic encapsulation.

## Key Features
1. **Health Endpoint**: A default health check endpoint is implemented to verify the application's status.
2. **OAuth 2.0 Authentication**: The application supports OAuth 2.0 for secure authentication and authorization.
3. **Azure Application Insights**: Logging is configured to send logs to Azure Application Insights using OpenTelemetry.
4. **Exception Handling**: Domain-specific exceptions are defined to handle errors gracefully.
5. **Standard Repository Structure**: The project follows a standard repository structure for maintainability and scalability.
6. **Code Linting**: Code quality is maintained using pylint, with configurations specified in `.pylintrc`.
7. **Unit Testing**: Unit tests are implemented using pytest, ensuring functionality and reliability.
8. **Docker Support**: A Dockerfile is provided for building the application image, with scanning capabilities for security.
9. **SOLID Principles**: The codebase adheres to SOLID design principles for better organization and maintainability.
10. **Azure Native Services**: The application utilizes Azure native services with managed identity for secure connections.

## Development Guidelines
- Follow the repository structure and naming conventions.
- Ensure all new features are covered by unit tests.
- Maintain code quality through linting and adherence to coding standards.
- Document any new functionality in the README.md file.
- Use Docker for local development and deployment.
- Never commit Terraform local runtime artifacts. Keep `.gitignore` enforcing exclusions for `.terraform/`, `terraform.tfstate*`, `tfplan*`, and crash/override Terraform files.

## Agent Skills — Mandatory Loading Rules

The following skills are available in `.github/skills/`. The agent **MUST** read
the relevant skill file via `read_file` **before** performing any task in that
domain, even when prior conversation context or summaries appear sufficient.
Summaries are a convenience — the skill file is the authoritative source.

| Domain | Trigger phrases | Agent(s) affected | Skill file to load |
|---|---|---|---|
| Terraform (write, review, fix, refactor, state) | "terraform", "tf code", "module", "variables", "outputs", "provider", "infra", "review tf", "best practices" | `infra-devops-agent`, `planning-agent` | `.github/skills/implement-tf-code/SKILL.md` |
| Cosmos DB repository (new entity, container, query) | "cosmos", "repository", "data access", "new container", "partition key", "async sdk" | `cosmosdb-repo-agent`, `python-coding-agent` | Invoked automatically via `repository_spec` in coding handoff |

### Loading procedure

1. Read `.github/skills/implement-tf-code/SKILL.md` first.
2. Identify which sub-documents apply to the task:
   - Style/naming → `coding-style.md`
   - New/modified module → `module-design.md`
   - Variable validation → `validation.md`
   - Tests → `testing.md`
   - State operations → `state-management.md`
   - Any `azurerm` resource → `azure-patterns.md`
3. Read those sub-documents before writing or editing any Terraform file.
4. Apply every rule found — do not rely on memory or conversation summaries as a substitute.

---

## Multi-Agent Orchestration

### Agent Roster

| Agent file | Name | Role | Invocable by |
|---|---|---|---|
| `orchestrator.agent.md` | `orchestrator-agent` | Drives the full workflow; owns no layer | User directly |
| `planning.agent.md` | `planning-agent` | Decomposes requirements into task lists | `orchestrator-agent` |
| `python-coding.agent.md` | `python-coding-agent` | Implements `src/` layer | `orchestrator-agent` |
| `database-implementation.agent.md` | `cosmosdb-repo-agent` | Implements `src/repository/` | `python-coding-agent` |
| `testing.agent.md` | `unit-test-agent` | Writes and runs tests in `tests/` | `orchestrator-agent` |
| `infra-devops.agent.md` | `infra-devops-agent` | Terraform + ACR + Container App deployment | `orchestrator-agent` |
| `azure-sre-agent.agent.md` | `azure-sre-agent` | Diagnoses Azure deployment failures | `orchestrator-agent` |

### Full Orchestration Workflow

```
User → orchestrator-agent
         │
         ├──[writes]──► v1__orchestrator__to__planner__<task>__run-NNN.json
         └──[invokes]──► planning-agent
                              │
                  ┌───────────┴───────────┐
                  │                       │
         [writes] ▼               [writes]▼
   v1__planner__to__coding__    v1__planner__to__infra__
   <task>__run-NNN.json         <task>__run-NNN.json
                  │                       │
                  ▼                       ▼
         python-coding-agent      infra-devops-agent   ← PARALLEL
          (+ cosmosdb-repo-agent   (Terraform + deploy)
             subagent)
                  │                       │
         [writes] ▼               [writes]▼
   v1__coding__to__testing__    v1__infra__to__orchestrator__
   <task>__run-NNN.json         <task>__run-NNN.json
                  │
                  ▼
           unit-test-agent
                  │
         [writes] ▼
   v1__testing__to__orchestrator__<task>__run-NNN.json
                  │
                  ▼
         orchestrator-agent  ←── collects both reports
                  │
         [health check /health]
                  │
        ┌─────────┴──────────┐
        │ OK                 │ FAIL
        ▼                    ▼
  run-summary         v1__orchestrator__to__sre__<task>__run-NNN.json
                           │
                           ▼
                     azure-sre-agent
                           │
                  [writes] ▼
                  v1__sre__to__planner__<task>__run-NNN.json
                           │
                           ▼
                     planning-agent  (re-plan, run-NNN++)
```

### Handoff File Naming Convention

```
v{version}__{sender}__to__{receiver}__{task-slug}__run-{NNN}.json
```

**Examples:**
- `v1__orchestrator__to__planner__add-transfer-api__run-001.json`
- `v1__planner__to__coding__add-transfer-api__run-001.json`
- `v1__infra__to__orchestrator__add-transfer-api__run-001.json`
- `v1__sre__to__planner__add-transfer-api__run-001.json`
- `v1__orchestrator__to__planner__add-transfer-api__run-002.json`  ← retry

### Handoff File Locations

| Directory | Purpose |
|---|---|
| `agents-communication/handoffs/` | Live handoff files for active runs |
| `agents-communication/handoffs/examples/` | Reference examples for all 8 file types |
| `agents-communication/schemas/` | JSON schemas — agents validate input/output against these |

### Quality Gates (enforced by orchestrator)

| Gate | Command | Pass condition |
|---|---|---|
| Lint | `pylint src/` | Exit code 0 |
| Tests | `pytest --cov=src --cov-fail-under=85` | All pass, coverage ≥ 85% |
| Security | `trivy image bankapi` | Zero HIGH/CRITICAL |
| Deployment health | `curl /health` | HTTP 200 + `status: healthy` |

---

## Custom Python Coding Agent Instructions
- The coding agent should assist in generating code snippets, implementing new features, and maintaining the repository according to the guidelines outlined above.
- It should prioritize adherence to SOLID principles and ensure that all code is well-documented and tested.
- The agent should facilitate integration with Azure services, ensuring that managed identities are used for secure connections.
- When operating inside the multi-agent workflow, always read the handoff file at the path given by the orchestrator — do not proceed from memory.

By following these instructions, developers can effectively contribute to the FastAPI Azure App project while maintaining high standards of code quality and functionality.