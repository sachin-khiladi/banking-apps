#!/usr/bin/env bash
# Expected env vars: TOKENS_USED, TOOL_NAME, OUTPUT_FILE, RAW_PROMPT
TOKENS=${TOKENS_USED:-0}
TOOL="${TOOL_NAME:-unknown}"
SESSION="${SESSION_ID:-unknown}"
MODEL="${MODEL:-unknown}"
TIMESTAMP="$(date -Iseconds)"
MASKED_PROMPT="$(./.github/hooks-scripts/mask-prompt.sh "${RAW_PROMPT:-}")"
# If OUTPUT_FILE exists, capture size
OUT_SIZE=0
if [ -n "${OUTPUT_FILE}" ] && [ -f "${OUTPUT_FILE}" ]; then
  if stat -f%z "$OUTPUT_FILE" >/dev/null 2>&1; then
    OUT_SIZE=$(stat -f%z "$OUTPUT_FILE")
  elif stat -c%s "$OUTPUT_FILE" >/dev/null 2>&1; then
    OUT_SIZE=$(stat -c%s "$OUTPUT_FILE")
  fi
fi
jq -c -n --arg t "$TIMESTAMP" --arg s "$SESSION" --arg m "$MODEL" --arg tool "$TOOL" --arg mp "$MASKED_PROMPT" --argjson tokens $TOKENS --argjson outsize $OUT_SIZE '{time:$t,session:$s,model:$m,tool:$tool,masked_prompt:$mp,tokens_used:$tokens,output_size_bytes:$outsize}' >> .copilot-logs/token-ops.jsonl
