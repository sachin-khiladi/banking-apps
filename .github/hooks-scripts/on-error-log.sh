#!/usr/bin/env bash
TIMESTAMP="$(date -Iseconds)"
MASKED_PROMPT="$(./.github/hooks-scripts/mask-prompt.sh "${RAW_PROMPT:-}")"
echo "{\"time\":\"$TIMESTAMP\",\"session\":\"${SESSION_ID:-unknown}\",\"error\":\"${ERROR_MSG:-unknown}\",\"masked_prompt\":\"$MASKED_PROMPT\"}" >> .copilot-logs/errors.jsonl
