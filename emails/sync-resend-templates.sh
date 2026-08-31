#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
CONFIG="${1:-$SCRIPT_DIR/templates.yaml}"

# Resolve relative config paths from the directory where the command was run,
# then run from the repository root so template paths have one stable base.
if [[ "$CONFIG" != /* ]]; then
  CONFIG="$PWD/$CONFIG"
fi
cd "$REPO_ROOT"

# This is the official environment variable consumed by the Resend CLI. Use a
# Full Access key in the local/CI template-sync environment.
if [[ -z "${RESEND_API_KEY:-}" ]]; then
  echo "ERROR: RESEND_API_KEY is required for template administration." >&2
  exit 1
fi

command -v resend >/dev/null 2>&1 || {
  echo "ERROR: Resend CLI is not installed." >&2
  exit 1
}

command -v yq >/dev/null 2>&1 || {
  echo "ERROR: yq is required to read $CONFIG." >&2
  exit 1
}

command -v npm >/dev/null 2>&1 || {
  echo "ERROR: npm is required to export the React Email templates." >&2
  exit 1
}

[[ -f "$CONFIG" ]] || {
  echo "ERROR: Config not found: $CONFIG" >&2
  exit 1
}

echo "Checking Resend..."
resend doctor

echo "Exporting React Email templates with Resend placeholders..."
(cd "$SCRIPT_DIR" && npm run export)

COUNT="$(yq -r '.templates | length' "$CONFIG")"

template_lookup_failure() {
  local alias="$1"
  local response="$2"
  local cli_status="$3"
  local http_status=""
  local error_name=""
  local message=""
  local category="unexpected API/CLI failure"

  # Resend's API errors are JSON objects. Extract only the fields needed for
  # classification; never echo the response, since it may contain request or
  # credential details.
  if printf '%s' "$response" | yq -e -p=json '.' >/dev/null 2>&1; then
    http_status="$(printf '%s' "$response" | yq -r -p=json \
      '.statusCode // .status // .error.statusCode // .error.status // ""' 2>/dev/null || true)"
    error_name="$(printf '%s' "$response" | yq -r -p=json \
      '.name // .code // .error.name // .error.code // ""' 2>/dev/null || true)"
    message="$(printf '%s' "$response" | yq -r -p=json \
      '.message // .error.message // ""' 2>/dev/null || true)"
  fi

  local normalized_name="${error_name,,}"
  local normalized_message="${message,,}"
  local normalized_response="${response,,}"

  # A 404/not_found response from `templates get <alias>` specifically means
  # that this template alias does not exist. No other failure may create it.
  if [[ "$http_status" == "404" ]]; then
    return 0
  fi

  if [[ "$http_status" == "401" || "$http_status" == "403" ||
        "$normalized_name" == *auth* || "$normalized_name" == "restricted_api_key" ]]; then
    category="authentication/authorization failure"
  elif [[ "$http_status" == "429" || "$normalized_name" == *rate_limit* ]]; then
    category="rate-limit failure"
  elif [[ "$http_status" == "400" || "$http_status" == "422" ]] &&
       [[ "$normalized_message" == *alias* ]]; then
    category="malformed alias"
  elif [[ "$normalized_response" == *"enotfound"* ||
          "$normalized_response" == *"econnrefused"* ||
          "$normalized_response" == *"econnreset"* ||
          "$normalized_response" == *"network"* ||
          "$normalized_response" == *"timed out"* ||
          "$normalized_response" == *"timeout"* ||
          "$normalized_response" == *"fetch failed"* ]]; then
    category="network failure"
  elif [[ -z "$http_status" ]]; then
    category="unstructured CLI failure"
  fi

  local status_detail=""
  [[ "$http_status" =~ ^[0-9]{3}$ ]] && status_detail=", HTTP $http_status"
  printf 'ERROR: Cannot check template alias %q: %s (CLI exit %s%s).\n' \
    "$alias" "$category" "$cli_status" "$status_detail" >&2
  return 1
}

for ((i = 0; i < COUNT; i++)); do
  ALIAS="$(yq -r ".templates[$i].alias" "$CONFIG")"
  NAME="$(yq -r ".templates[$i].name" "$CONFIG")"
  SUBJECT="$(yq -r ".templates[$i].subject" "$CONFIG")"
  FILE="$(yq -r ".templates[$i].file" "$CONFIG")"
  HTML_FILE="$(yq -r ".templates[$i].html_file" "$CONFIG")"
  PUBLISH="$(yq -r ".templates[$i].publish" "$CONFIG")"
  [[ "$PUBLISH" == "null" ]] && PUBLISH="true"

  echo
  echo "→ Syncing: $ALIAS"

  [[ -f "$FILE" ]] || {
    echo "ERROR: Template file not found: $FILE" >&2
    exit 1
  }
  [[ -f "$HTML_FILE" ]] || {
    echo "ERROR: Rendered template not found: $HTML_FILE" >&2
    exit 1
  }

  mapfile -t VARIABLES < <(
    yq -r ".templates[$i].variables // {} | to_entries | .[] | \"\(.key):\(.value)\"" "$CONFIG"
  )
  VAR_ARGS=()
  for VARIABLE in "${VARIABLES[@]}"; do
    VAR_ARGS+=(--var "$VARIABLE")
  done

  GET_RESPONSE=""
  GET_STATUS=0
  if GET_RESPONSE="$(resend templates get "$ALIAS" --json 2>&1)"; then
    echo "  Updating existing template..."
    resend templates update "$ALIAS" \
      --name "$NAME" \
      --subject "$SUBJECT" \
      --html-file "$HTML_FILE" \
      "${VAR_ARGS[@]}"
  else
    GET_STATUS=$?
    if template_lookup_failure "$ALIAS" "$GET_RESPONSE" "$GET_STATUS"; then
      echo "  Creating template..."
      resend templates create \
        --alias "$ALIAS" \
        --name "$NAME" \
        --subject "$SUBJECT" \
        --html-file "$HTML_FILE" \
        "${VAR_ARGS[@]}"
    else
      exit "$GET_STATUS"
    fi
  fi

  if [[ "$PUBLISH" == "true" ]]; then
    echo "  Publishing..."
    resend templates publish "$ALIAS"
  fi

  echo "  ✓ $ALIAS"
done

echo
echo "All Resend templates synced."
