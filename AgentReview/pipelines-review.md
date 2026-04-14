# DevOps Pipelines Code Review (GPT-5.3-Codex)

Scope: read-only review of GitHub Actions and Azure DevOps YAML pipeline definitions.

## CI-001
- Severity: High
- Category: SupplyChain
- Location: `.github/workflows/workflow-build-v1.0.0.yml:64`, `.github/workflows/infra-apply-dev.yml:44`, `.github/workflows/infra-apply-prod.yml:39`, `.github/workflows/infra-terraform.yml:49`
- Rule: Third-party CI actions should be pinned to immutable commit SHAs, not moving major tags.
- Evidence: Multiple actions use mutable references such as `actions/checkout@v4` and `hashicorp/setup-terraform@v3`.
- Impact: Upstream action tag movement can introduce unreviewed behavioral changes into trusted deployment paths.
- Recommendation: Pin all external actions to commit SHA and manage upgrades through periodic dependency refresh PRs.
- Grounding: CI/CD supply-chain hardening standards require immutable dependencies in privileged automation contexts.

## CI-002
- Severity: High
- Category: Security
- Location: `.github/workflows/cd.yml:54`, `.github/workflows/cd.yml:80`
- Rule: Deployment pipelines should verify image integrity/provenance before promotion.
- Evidence: `verify_image: false` is passed for both dev and prod deploy jobs, bypassing integrity verification step in reusable deploy workflow.
- Impact: Pipeline can deploy unsigned/unverified images if registry compromise or tagging error occurs.
- Recommendation: Set `verify_image: true` at minimum for prod; preferably enforce true for all environments and fail closed on missing attestations.
- Grounding: Artifact verification is a core release control preventing tampered or untrusted container images from reaching runtime.

## CI-003
- Severity: Medium
- Category: SupplyChain
- Location: `pipelines/tf-infra-plan.yml:85`, `pipelines/tf-infra-plan.yml:259`, `pipelines/tf-infra-apply.yml:84`, `pipelines/tf-infra-apply.yml:244`
- Rule: Downloaded tool binaries in CI must be integrity-verified before execution.
- Evidence: Terraform binary zip is downloaded via `wget` and unzipped/executed without checksum or signature validation.
- Impact: Network/path compromise or upstream artifact substitution could execute malicious binaries with pipeline credentials.
- Recommendation: Verify SHA256 checksum from HashiCorp release checksums (or use a trusted installer/task that enforces integrity).
- Grounding: Build/deploy runners are high-trust execution planes; unsigned binary execution is a recognized software supply-chain risk.
