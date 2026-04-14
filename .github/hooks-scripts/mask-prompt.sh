#!/usr/bin/env bash
# Usage: mask-prompt.sh "<raw prompt>"
PROMPT="$1"
# Keep only first 80 chars and replace non-space sequences after 80 chars with "[MASKED]"
MASKED="$(printf '%s' "$PROMPT" | sed -E 's/^(.{80}).*/\1 [MASKED]/')"
# Remove any obvious secrets patterns like tokens or keys
MASKED="$(printf '%s' "$MASKED" | sed -E 's/([A-Za-z0-9_\-]{20,})/[REDACTED]/g')"
printf '%s' "$MASKED"
