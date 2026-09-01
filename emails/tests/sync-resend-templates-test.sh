#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
SYNC_SCRIPT="$SCRIPT_DIR/../sync-resend-templates.sh"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

mkdir -p "$TMP_DIR/bin"
touch "$TMP_DIR/template.tsx"
printf '{{{USER_NAME}}}\n' >"$TMP_DIR/template.html"
cat >"$TMP_DIR/templates.yaml" <<EOF
templates:
  - alias: test-alias
    name: Test
    subject: Test subject
    file: $TMP_DIR/template.tsx
    html_file: $TMP_DIR/template.html
    variables:
      USER_NAME:
        type: string
        fallback: researcher
      LOGIN_URL: string
    publish: false
EOF

cat >"$TMP_DIR/bin/yq" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
args="$*"

if [[ "$args" == '--version' ]]; then
  echo 'yq (https://github.com/mikefarah/yq/) version v4.45.1'
  exit 0
fi

input="$(cat || true)"

if [[ "$args" == *'-p=json'* ]]; then
  [[ "$input" == \{*\} ]] || exit 1
  if [[ "$args" == *statusCode* ]]; then
    sed -n 's/.*"statusCode"[[:space:]]*:[[:space:]]*\([0-9][0-9]*\).*/\1/p' <<<"$input"
  elif [[ "$args" == *'.name'* ]]; then
    sed -n 's/.*"name"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' <<<"$input"
  elif [[ "$args" == *'.message'* ]]; then
    sed -n 's/.*"message"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' <<<"$input"
  elif [[ "$args" == *'.data[].alias'* ]]; then
    grep -o '"alias"[[:space:]]*:[[:space:]]*"[^"]*"' <<<"$input" |
      sed 's/.*"alias"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/'
  fi
  exit 0
fi

case "$args" in
  *'.templates | length'*) echo 1 ;;
  *'.templates[0].alias'*) echo test-alias ;;
  *'.templates[0].name'*) echo Test ;;
  *'.templates[0].subject'*) echo 'Test subject' ;;
  *'.templates[0].file'*) echo "$MOCK_TEMPLATE_FILE" ;;
  *'.templates[0].html_file'*) echo "$MOCK_HTML_FILE" ;;
  *'.templates[0].variables'*to_entries*)
    printf 'USER_NAME:string:researcher\nLOGIN_URL:string\n'
    ;;
  *'.templates[0].publish'*) echo false ;;
  *) exit 2 ;;
esac
EOF
chmod +x "$TMP_DIR/bin/yq"

run_case() {
  local scenario="$1"
  local output_file="$TMP_DIR/$scenario.output"
  local calls_file="$TMP_DIR/$scenario.calls"
  : >"$calls_file"

  cat >"$TMP_DIR/bin/npm" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
printf 'npm %s\n' "$*" >>"$MOCK_CALLS_FILE"
EOF
  chmod +x "$TMP_DIR/bin/npm"

  cat >"$TMP_DIR/bin/resend" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' "$*" >>"$MOCK_CALLS_FILE"
[[ "${1:-}" == doctor ]] && exit 0

if [[ "$*" == 'templates get test-alias --json' ]]; then
  printf 'unexpected templates get call\n' >&2
  exit 1
fi

if [[ "$*" == 'templates list --json --limit 100' ]]; then
  case "$MOCK_SCENARIO" in
    existing) printf '{"data":[{"id":"template-id","alias":"test-alias"}]}\n'; exit 0 ;;
    missing) printf '{"data":[]}\n'; exit 0 ;;
    authentication) printf '{"error":{"statusCode":401,"code":"fetch_error","message":"API key secret-value is invalid"}}\n' >&2; exit 1 ;;
    network) printf 'Fetch failed: ECONNREFUSED secret-response-body\n' >&2; exit 1 ;;
  esac
fi
exit 0
EOF
  chmod +x "$TMP_DIR/bin/resend"

  set +e
  PATH="$TMP_DIR/bin:$PATH" \
    YQ="$TMP_DIR/bin/yq" \
    RESEND_API_KEY='re_secret_sync_key' \
    MOCK_SCENARIO="$scenario" \
    MOCK_CALLS_FILE="$calls_file" \
    MOCK_TEMPLATE_FILE="$TMP_DIR/template.tsx" \
    MOCK_HTML_FILE="$TMP_DIR/template.html" \
    "$SYNC_SCRIPT" "$TMP_DIR/templates.yaml" >"$output_file" 2>&1
  CASE_STATUS=$?
  set -e
  CASE_OUTPUT="$output_file"
  CASE_CALLS="$calls_file"
}

run_case existing
[[ "$CASE_STATUS" == 0 ]]
grep -qx 'npm run export' "$CASE_CALLS"
grep -qx 'templates list --json --limit 100' "$CASE_CALLS"
grep -q 'templates update test-alias --name Test --subject Test subject --html-file .*template.html --var USER_NAME:string:researcher --var LOGIN_URL:string' "$CASE_CALLS"
! grep -q 'templates create' "$CASE_CALLS"

run_case missing
[[ "$CASE_STATUS" == 0 ]]
grep -q '^templates create --alias test-alias .*--html-file .*template.html --var USER_NAME:string:researcher --var LOGIN_URL:string' "$CASE_CALLS"

run_case authentication
[[ "$CASE_STATUS" != 0 ]]
grep -q 'authentication/authorization failure' "$CASE_OUTPUT"
! grep -q 'templates create' "$CASE_CALLS"
! grep -q 'secret-value\|re_secret_sync_key' "$CASE_OUTPUT"

run_case network
[[ "$CASE_STATUS" != 0 ]]
grep -q 'network failure' "$CASE_OUTPUT"
! grep -q 'templates create' "$CASE_CALLS"
! grep -q 'secret-response-body\|re_secret_sync_key' "$CASE_OUTPUT"

set +e
PATH="$TMP_DIR/bin:$PATH" \
  YQ="$TMP_DIR/bin/yq" \
  "$SYNC_SCRIPT" "$TMP_DIR/templates.yaml" >"$TMP_DIR/runtime-only.output" 2>&1
RUNTIME_ONLY_STATUS=$?
set -e
[[ "$RUNTIME_ONLY_STATUS" != 0 ]]
grep -q 'RESEND_API_KEY is required' "$TMP_DIR/runtime-only.output"

echo 'sync-resend-templates mocked checks passed'
