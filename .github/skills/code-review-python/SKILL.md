---
name: code-review-python
description: >
  Perform an industry-grade technical code review for Python application code.
  Scope is read-only analysis of source files and writing findings to AgentReview output.
model: GPT-5.3-Codex
filePatterns:
  - "src/**/*.py"
  - "tests/**/*.py"
mode: read-only
---

# Python Code Review Skill (Read-Only)

## Purpose
Run a technical Python review against security, reliability, correctness, maintainability,
and observability standards suitable for production FinTech workloads.

## Mandatory Operating Rules
1. Use GPT-5.3-Codex for review reasoning and recommendations.
2. Read-only repository operations only (search/read/list). Do not modify source files.
3. Report only evidence-backed findings with exact file path and line references.
4. Prefer high-signal findings (defects/risk) over style-only comments.

## Review Checks (Industry Accepted)
- API error handling boundaries (domain exception mapping, no opaque catch-all paths)
- AuthN/AuthZ hardening (secret handling, token validation assumptions, role checks)
- Secret and credential hygiene (no insecure defaults in runtime paths)
- Async/resource lifecycle safety (client/session creation/closure patterns)
- Logging/telemetry quality (traceability, no sensitive data leakage)
- Contract quality (typing, docstrings, deterministic return/error contracts)

## Finding Format (required)
For each finding, use this structure:
- ID: PY-###
- Severity: Critical | High | Medium | Low
- Category: Security | Reliability | Correctness | Maintainability | Observability
- Location: <path>:<line>
- Rule: <industry rule or control objective>
- Evidence: <what code does currently>
- Impact: <failure mode / exploitability / operational risk>
- Recommendation: <precise remediation>
- Grounding: <why this is requested; engineering/security rationale>

## Output Contract
Write findings to:
- AgentReview/python-review.md

If no issues are found, write a PASS report with explicit checks executed.
