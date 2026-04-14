#!/usr/bin/env bash
# Expected env vars: ESTIMATED_TOKENS, REMAINING_TOKENS, TOOL_NAME
THRESHOLD_PERCENT=${TOKEN_THRESHOLD_PERCENT:-90}
REMAINING=${REMAINING_TOKENS:-0}
ESTIMATED=${ESTIMATED_TOKENS:-0}
# Deny if estimated tokens exceed remaining or exceed threshold of initial budget
if [ "$ESTIMATED" -gt "$REMAINING" ]; then
  echo "{\"time\":\"$(date -Iseconds)\",\"session\":\"${SESSION_ID:-unknown}\",\"tool\":\"${TOOL_NAME:-unknown}\",\"action\":\"deny\",\"reason\":\"estimated tokens exceed remaining\",\"estimated\":$ESTIMATED,\"remaining\":$REMAINING}" >> .copilot-logs/pre-tool-deny.jsonl
  exit 1
fi
# Optional: deny if estimated would push usage above threshold of initial budget
if [ -n "${INITIAL_TOKEN_BUDGET}" ] && [ "$(( (INITIAL_TOKEN_BUDGET - REMAINING + ESTIMATED) * 100 / INITIAL_TOKEN_BUDGET ))" -ge "$THRESHOLD_PERCENT" ]; then
  echo "{\"time\":\"$(date -Iseconds)\",\"session\":\"${SESSION_ID:-unknown}\",\"tool\":\"${TOOL_NAME:-unknown}\",\"action\":\"deny\",\"reason\":\"would exceed token threshold\",\"estimated\":$ESTIMATED,\"remaining\":$REMAINING,\"threshold_percent\":$THRESHOLD_PERCENT}" >> .copilot-logs/pre-tool-deny.jsonl
  exit 1
fi
# Allow
echo "{\"time\":\"$(date -Iseconds)\",\"session\":\"${SESSION_ID:-unknown}\",\"tool\":\"${TOOL_NAME:-unknown}\",\"action\":\"allow\",\"estimated\":$ESTIMATED,\"remaining\":$REMAINING}" >> .copilot-logs/pre-tool-allow.jsonl
exit 0
