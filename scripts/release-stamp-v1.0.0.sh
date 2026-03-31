#!/usr/bin/env bash
set -euo pipefail

OUTPUT_FILE="${1:-release-stamp.json}"
ENVIRONMENT="${2:-dev}"
BRANCH_NAME="${3:-unknown}"
COMMIT_SHA="${4:-unknown}"
PIPELINE_NAME="${5:-unknown}"
ADDITIONAL_TAGS="${6:-}"

TIMESTAMP_UTC="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
IFS=',' read -ra TAG_ARRAY <<< "$ADDITIONAL_TAGS"

TAGS_JSON="[\"environment:${ENVIRONMENT}\",\"branch:${BRANCH_NAME}\",\"pipeline:${PIPELINE_NAME}\",\"timestamp:${TIMESTAMP_UTC}\""
for tag in "${TAG_ARRAY[@]}"; do
  cleaned="$(echo "$tag" | xargs)"
  if [[ -n "$cleaned" ]]; then
    TAGS_JSON+=" ,\"${cleaned}\""
  fi
done
TAGS_JSON+="]"

cat > "$OUTPUT_FILE" <<EOF
{
  "releaseStampVersion": "1.0.0",
  "environment": "${ENVIRONMENT}",
  "branch": "${BRANCH_NAME}",
  "commit": "${COMMIT_SHA}",
  "pipeline": "${PIPELINE_NAME}",
  "createdUtc": "${TIMESTAMP_UTC}",
  "tags": ${TAGS_JSON}
}
EOF

echo "release stamp created at ${OUTPUT_FILE}"
