---
name: code-review-devops-pipelines
description: >
  Perform an industry-grade technical review of CI/CD pipelines for GitHub Actions
  and Azure DevOps YAML definitions. Read-only analysis only.
model: GPT-5.3-Codex
filePatterns:
  - ".github/workflows/**/*.yml"
  - ".github/workflows/**/*.yaml"
  - "pipelines/**/*.yml"
  - "pipelines/**/*.yaml"
mode: read-only
---

# DevOps Pipeline Code Review Skill (Read-Only)

## Purpose
Assess CI/CD pipelines for supply-chain security, deployment safety, and release governance.

## Mandatory Operating Rules
1. Use GPT-5.3-Codex for technical review.
2. Read-only repository analysis only.
3. Findings must be evidence-backed with exact file+line references.
4. Prioritize controls that reduce breach and outage blast radius.

## Review Checks (Industry Accepted)
- Action/task pinning strategy (immutable pinning vs floating versions)
- Identity and permissions (OIDC, least privilege, secret minimization)
- Promotion and environment gates (infra-first sequencing, approvals, branch policies)
- Concurrency/race prevention in deploy jobs
- Artifact integrity verification before deployment
- Script hardening (checksum verification for downloaded tools)

## Finding Format (required)
- ID: CI-###
- Severity: Critical | High | Medium | Low
- Category: Security | SupplyChain | Reliability | Governance
- Location: <path>:<line>
- Rule: <industry rule or control objective>
- Evidence: <current implementation>
- Impact: <threat/failure mode>
- Recommendation: <precise pipeline remediation>
- Grounding: <why this requirement exists>

## Output Contract
Write findings to:
- AgentReview/pipelines-review.md

If no issues are found, write a PASS report with explicit checks executed.
