#!/usr/bin/env bash
TIMESTAMP="$(date -Iseconds)"
echo "{\"time\":\"$TIMESTAMP\",\"session\":\"${SESSION_ID:-unknown}\",\"total_tokens_used\":${TOTAL_TOKENS_USED:-0}}" >> .copilot-logs/session-end.jsonl
