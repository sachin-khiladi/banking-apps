#!/usr/bin/env bash
mkdir -p .copilot-logs
TIMESTAMP="$(date -Iseconds)"
echo "{\"time\":\"$TIMESTAMP\",\"session\":\"${SESSION_ID:-unknown}\",\"model\":\"${MODEL:-unknown}\",\"initial_token_budget\":${INITIAL_TOKEN_BUDGET:-null}}" >> .copilot-logs/session-start.jsonl
