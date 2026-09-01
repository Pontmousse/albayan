#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
CONFIG="${1:-$SCRIPT_DIR/templates.yaml}"

# Resolve relative config paths from where the command was invoked.
if [[ "$CONFIG" != /* ]]; then
  CONFIG="$PWD/$CONFIG"
fi

cd "$REPO_ROOT"

if [[ -z "${RESEND_API_KEY:-}" ]]; then
  echo "ERROR: RESEND_API_KEY is required for template administration." >&2
  exit 1
fi

command -v resend >/dev/null 2>&1 || {
  echo "ERROR: Resend CLI is not installed." >&2
  exit 1
}

# Explicitly require Mike Farah yq v4; tests and CI may override YQ.
if [[ -z "${YQ:-}" ]]; then
  if [[ -x /snap/bin/yq ]]; then
    YQ=/snap/bin/yq
  else
    YQ="$(command -v yq || true)"
  fi
fi

[[ -n "$YQ" && -x "$YQ" ]] || {
  echo "ERROR: Mike Farah yq v4 was not found in PATH." >&2
  exit 1
}

YQ_VERSION="$("$YQ" --version 2>&1 || true)"
if [[ "$YQ_VERSION" != *"mikefarah/yq"* || "$YQ_VERSION" != *"version v4."* ]]; then
  echo "ERROR: Template sync requires Mike Farah yq v4 (not Python yq)." >&2
  exit 1
fi

command -v npm >/dev/null 2>&1 || {
  echo "ERROR: npm is required to export React Email templates." >&2
  exit 1
}

[[ -f "$CONFIG" ]] || {
  echo "ERROR: Config not found: $CONFIG" >&2
  exit 1
}

echo "Checking Resend..."
resend doctor

echo
echo "Exporting React Email templates with Resend placeholders..."

(
  cd "$SCRIPT_DIR"
  npm run export
)

COUNT="$("$YQ" -r '.templates | length' "$CONFIG")"

if [[ "$COUNT" == "0" ]]; then
  echo "No templates configured."
  exit 0
fi

redact_resend_output() {
  sed -E \
    -e "s/${RESEND_API_KEY//\//\\/}/[REDACTED_RESEND_API_KEY]/g" \
    -e 's/re_[A-Za-z0-9_=-]+/[REDACTED_RESEND_API_KEY]/g' \
    -e 's/secret-[^[:space:]]+/[REDACTED_SECRET]/g'
}

echo
echo "Fetching existing Resend templates..."

# Read every page so an alias beyond the default first 10 results is not
# mistaken for a missing template and sent to the create endpoint.
EXISTING_ALIASES=()
AFTER_CURSOR=""

while true; do
  LIST_ARGS=(templates list --json --limit 100)
  if [[ -n "$AFTER_CURSOR" ]]; then
    LIST_ARGS+=(--after "$AFTER_CURSOR")
  fi

  if ! RAW_TEMPLATES_OUTPUT="$(resend "${LIST_ARGS[@]}" 2>&1)"; then
    normalized_response="$(printf '%s' "$RAW_TEMPLATES_OUTPUT" | tr '[:upper:]' '[:lower:]')"
    if [[ "$normalized_response" == *"unauthorized"* ||
          "$normalized_response" == *"forbidden"* ||
          "$normalized_response" == *"invalid"* ]]; then
      echo "ERROR: Resend template list failed due to authentication/authorization failure." >&2
    else
      echo "ERROR: Resend template list failed due to network failure." >&2
    fi
    printf '%s\n' "$RAW_TEMPLATES_OUTPUT" | redact_resend_output >&2
    exit 1
  fi

  TEMPLATES_JSON="$(
    printf '%s\n' "$RAW_TEMPLATES_OUTPUT" |
      sed -n '/^[[:space:]]*{/,$p'
  )"

  if [[ -z "$TEMPLATES_JSON" ]]; then
    echo "ERROR: Resend returned no JSON when listing templates." >&2
    echo "Raw output:" >&2
    printf '%s\n' "$RAW_TEMPLATES_OUTPUT" | redact_resend_output >&2
    exit 1
  fi

  if ! printf '%s' "$TEMPLATES_JSON" |
    "$YQ" -e -p=json '.' - >/dev/null 2>&1; then

    echo "ERROR: Could not parse 'resend templates list --json' output." >&2
    echo "Raw output:" >&2
    printf '%s\n' "$RAW_TEMPLATES_OUTPUT" | redact_resend_output >&2
    exit 1
  fi

  mapfile -t PAGE_ALIASES < <(
    printf '%s' "$TEMPLATES_JSON" |
      "$YQ" -r -p=json '.data[].alias' -
  )
  EXISTING_ALIASES+=("${PAGE_ALIASES[@]}")

  HAS_MORE="$(
    printf '%s' "$TEMPLATES_JSON" |
      "$YQ" -r -p=json '.has_more // false' -
  )"
  if [[ "$HAS_MORE" != "true" ]]; then
    break
  fi

  AFTER_CURSOR="$(
    printf '%s' "$TEMPLATES_JSON" |
      "$YQ" -r -p=json '.data[-1].id // ""' -
  )"
  if [[ -z "$AFTER_CURSOR" ]]; then
    echo "ERROR: Resend reported another template page without a cursor." >&2
    exit 1
  fi
done

template_exists() {
  local wanted_alias="$1"
  local existing_alias

  for existing_alias in "${EXISTING_ALIASES[@]}"; do
    if [[ "$existing_alias" == "$wanted_alias" ]]; then
      return 0
    fi
  done

  return 1
}

for ((i = 0; i < COUNT; i++)); do
  ALIAS="$("$YQ" -r ".templates[$i].alias" "$CONFIG")"
  NAME="$("$YQ" -r ".templates[$i].name" "$CONFIG")"
  SUBJECT="$("$YQ" -r ".templates[$i].subject" "$CONFIG")"
  FILE="$("$YQ" -r ".templates[$i].file" "$CONFIG")"
  HTML_FILE="$("$YQ" -r ".templates[$i].html_file" "$CONFIG")"
  PUBLISH="$("$YQ" -r ".templates[$i].publish // true" "$CONFIG")"

  echo
  echo "→ Syncing: $ALIAS"

  if [[ -z "$ALIAS" || "$ALIAS" == "null" ]]; then
    echo "ERROR: Template at index $i is missing 'alias'." >&2
    exit 1
  fi

  if [[ -z "$NAME" || "$NAME" == "null" ]]; then
    echo "ERROR: Template '$ALIAS' is missing 'name'." >&2
    exit 1
  fi

  if [[ -z "$SUBJECT" || "$SUBJECT" == "null" ]]; then
    echo "ERROR: Template '$ALIAS' is missing 'subject'." >&2
    exit 1
  fi

  if [[ -z "$FILE" || "$FILE" == "null" ]]; then
    echo "ERROR: Template '$ALIAS' is missing 'file'." >&2
    exit 1
  fi

  if [[ -z "$HTML_FILE" || "$HTML_FILE" == "null" ]]; then
    echo "ERROR: Template '$ALIAS' is missing 'html_file'." >&2
    exit 1
  fi

  [[ -f "$FILE" ]] || {
    echo "ERROR: Template source file not found: $FILE" >&2
    exit 1
  }

  [[ -f "$HTML_FILE" ]] || {
    echo "ERROR: Rendered template not found: $HTML_FILE" >&2
    exit 1
  }

  mapfile -t VARIABLES < <(
    "$YQ" -r "
      .templates[$i].variables // {}
      | to_entries
      | .[]
      | [.key, (.value.type // .value), .value.fallback]
      | map(select(. != null))
      | join(\":\")
    " "$CONFIG"
  )

  VAR_ARGS=()

  for VARIABLE in "${VARIABLES[@]}"; do
    VAR_ARGS+=(--var "$VARIABLE")
  done

  if template_exists "$ALIAS"; then
    echo "  Updating existing template..."

    resend templates update "$ALIAS" \
      --name "$NAME" \
      --subject "$SUBJECT" \
      --html-file "$HTML_FILE" \
      "${VAR_ARGS[@]}"
  else
    echo "  Creating template..."

    resend templates create \
      --alias "$ALIAS" \
      --name "$NAME" \
      --subject "$SUBJECT" \
      --html-file "$HTML_FILE" \
      "${VAR_ARGS[@]}"

    # Remember it locally in case the config somehow references it again.
    EXISTING_ALIASES+=("$ALIAS")
  fi

  if [[ "$PUBLISH" == "true" ]]; then
    echo "  Publishing..."
    resend templates publish "$ALIAS"
  else
    echo "  Leaving as draft."
  fi

  echo "  ✓ $ALIAS"
done

echo
echo "All Resend templates synced."


# Run like this:
# YQ=/snap/bin/yq npm run templates:sync
