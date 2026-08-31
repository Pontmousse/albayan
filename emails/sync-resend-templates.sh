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

# Use the dedicated Full Access credential for local/CI synchronization while
# leaving RESEND_API_KEY as the backend runtime/send credential.
if [[ -n "${RESEND_TEMPLATE_SYNC_API_KEY:-}" ]]; then
  export RESEND_API_KEY="$RESEND_TEMPLATE_SYNC_API_KEY"
fi

if [[ -z "${RESEND_API_KEY:-}" ]]; then
  echo "ERROR: RESEND_TEMPLATE_SYNC_API_KEY or RESEND_API_KEY is required." >&2
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

[[ -f "$CONFIG" ]] || {
  echo "ERROR: Config not found: $CONFIG" >&2
  exit 1
}

echo "Checking Resend..."
resend doctor

# Render the React Email sources with their placeholder defaults. Uploading the
# resulting HTML avoids the CLI replacing those defaults while compiling TSX.
(cd "$SCRIPT_DIR" && npm run export)

COUNT="$(yq -r '.templates | length' "$CONFIG")"

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

  if resend templates get "$ALIAS" >/dev/null 2>&1; then
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
  fi

  if [[ "$PUBLISH" == "true" ]]; then
    echo "  Publishing..."
    resend templates publish "$ALIAS"
  fi

  echo "  ✓ $ALIAS"
done

echo
echo "All Resend templates synced."
