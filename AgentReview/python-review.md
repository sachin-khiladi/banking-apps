# Python Code Review (GPT-5.3-Codex)

Scope: read-only review of `src/**/*.py`

## PY-001
- Severity: High
- Category: Security
- Location: `src/auth/oauth2.py:33`
- Rule: Cryptographic signing secrets must be fail-closed in non-test runtime paths (no insecure fallback values).
- Evidence: `SECRET_KEY` defaults to `"local-dev-insecure-secret"` when `JWT_SECRET_KEY` is absent.
- Impact: Any deployment missing `JWT_SECRET_KEY` silently signs/validates JWTs with a predictable key, enabling token forgery and full auth bypass.
- Recommendation: Remove insecure default and fail startup when `JWT_SECRET_KEY` is unset (except in explicit test mode guarded by environment flag).
- Grounding: Industry auth controls require deterministic secret management and fail-closed behavior to prevent silent downgrade of authentication trust.

## PY-002
- Severity: Medium
- Category: Reliability
- Location: `src/api/accounts.py:107`, `src/api/profile.py:92`, `src/api/statements.py:84`
- Rule: API boundaries should avoid broad catch-all exception handling without structured logging of original failure context.
- Evidence: Route handlers catch `Exception` and map through `_raise_http`, returning generic 500 for unexpected cases.
- Impact: Root-cause telemetry is suppressed at API boundary; operational triage becomes slower and repeated incidents are harder to correlate.
- Recommendation: Catch known domain exceptions explicitly, log unexpected exceptions with structured context (`request_id`, route, actor), then return sanitized 500.
- Grounding: Production incident response standards require preserving diagnostic context while maintaining safe client-facing error envelopes.

## PY-003
- Severity: Medium
- Category: Reliability
- Location: `src/repository/cosmos_account_repository.py:68`, `src/repository/cosmos_user_profile_repository.py:65`
- Rule: Async credentials/resources must be lifecycle-managed to avoid descriptor/socket accumulation.
- Evidence: `_new_client()` instantiates `DefaultAzureCredential()` per call and returns `CosmosClient`; credential object is not explicitly closed.
- Impact: Under sustained load, repeated credential creation can increase token acquisition overhead and resource pressure.
- Recommendation: Reuse a long-lived credential/client via dependency injection and close once during app shutdown, or ensure explicit credential close semantics in repository lifecycle.
- Grounding: Cloud SDK best practices for high-throughput services favor controlled client/credential reuse to improve latency stability and reduce runtime churn.
