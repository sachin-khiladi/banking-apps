---
name: code-review-terraform
description: >
  Perform an industry-grade technical review of Terraform code for security,
  resilience, and infrastructure correctness. Read-only analysis only.
model: GPT-5.3-Codex
filePatterns:
  - "infra/**/*.tf"
mode: read-only
---

# Terraform Code Review Skill (Read-Only)

## Purpose
Review Terraform code for production readiness with emphasis on policy compliance,
change safety, and cloud security posture.

## Mandatory Operating Rules
1. Use GPT-5.3-Codex for review decisions.
2. Read-only operations only; do not edit terraform files during review.
3. Every finding must cite concrete evidence with file+line references.
4. Distinguish design intent from actual enforced controls.

## Review Checks (Industry Accepted)
- Input validation strength (regex rigor, immutable-tag or digest constraints)
- Lifecycle safety (`ignore_changes`, preconditions, drift ownership boundaries)
- Identity and access model (least privilege, managed identities, RBAC scope)
- Secret handling (`sensitive = true`, no secret outputs)
- Provider/backend posture (version constraints, remote state safety)
- Tagging, governance, and environment parity controls

## Finding Format (required)
- ID: TF-###
- Severity: Critical | High | Medium | Low
- Category: Security | Reliability | Correctness | Governance
- Location: <path>:<line>
- Rule: <industry rule or control objective>
- Evidence: <what is implemented>
- Impact: <operational/security risk>
- Recommendation: <precise Terraform-level remediation>
- Grounding: <why this control matters>

## Output Contract
Write findings to:
- AgentReview/terraform-review.md

If no issues are found, write a PASS report with explicit checks executed.
