---
name: implement-tf-code
description: >
  Implement, update, delete, query, and manage state for Terraform code in this
  repository. Use this skill whenever the user asks about Terraform coding,
  module authoring, variable design, validation rules, testing, or state
  organisation. This skill focuses exclusively on **coding** — not deployment
  or CI/CD execution.
---

# Terraform Coding Skill

This skill provides structured guidance for writing production-quality Terraform
code. It is split into focused sub-documents — read only the section(s) relevant
to the task at hand.

## Quick Reference

| Topic | File | When to use |
|---|---|---|
| Code style & formatting | [coding-style.md](coding-style.md) | Naming, layout, `fmt`, `validate`, linting |
| Module design | [module-design.md](module-design.md) | File structure, inputs/outputs, composition |
| Validation & conditions | [validation.md](validation.md) | `variable` validation, `precondition`, `postcondition`, `check` |
| Testing | [testing.md](testing.md) | `.tftest.hcl` unit & integration tests |
| State management | [state-management.md](state-management.md) | Remote state, workspaces, `moved`, `import` |
| Azure provider patterns | [azure-patterns.md](azure-patterns.md) | `azurerm` idioms, UAMI, RBAC, naming, imports |

## Ground Rules

1. **Read the relevant sub-document first** before generating or editing any
   Terraform code.
2. Apply every rule in [coding-style.md](coding-style.md) by default.
3. When authoring or modifying a module, follow [module-design.md](module-design.md).
4. Validate logic with the patterns in [validation.md](validation.md).
5. Write or update tests per [testing.md](testing.md) whenever logic changes.
6. Use Azure-specific idioms from [azure-patterns.md](azure-patterns.md) for all
   `azurerm` resources.

## Scope

- Target Terraform ≥ **1.6** (native test framework) with `azurerm` ≥ **3.x**.
- Workspace layout: `infra/environments/<env>/` (root modules) and
  `infra/modules/<name>/` (child modules).
- Focus is **code quality** — no deployment commands, no pipeline steps.