#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
RUNTIME_ROOT="${RUNTIME_ROOT:-$REPO_ROOT/.runtime/dev-web}"
WATCHDOG_LOG="${WATCHDOG_LOG:-$RUNTIME_ROOT/watchdog.log}"
NVM_DIR="${NVM_DIR:-$HOME/.nvm}"
CRON_LINE="* * * * * NVM_DIR=$NVM_DIR PATH=/usr/local/bin:/usr/bin:/bin cd $REPO_ROOT && ./deploy/ensure-dev-web-pm2.sh --quiet >> $WATCHDOG_LOG 2>&1"
TMP_CRON="$(mktemp)"

trap 'rm -f "$TMP_CRON"' EXIT

mkdir -p "$RUNTIME_ROOT"

if crontab -l >"$TMP_CRON" 2>/dev/null; then
  :
else
  : >"$TMP_CRON"
fi

if rg -n "ensure-dev-web-pm2\\.sh" "$TMP_CRON" >/dev/null 2>&1; then
  rg -v "ensure-dev-web-pm2\\.sh" "$TMP_CRON" > "$TMP_CRON.filtered"
  mv "$TMP_CRON.filtered" "$TMP_CRON"
fi

if rg -Fqx "$CRON_LINE" "$TMP_CRON"; then
  echo "✓ dev 웹 watchdog cron이 이미 등록되어 있습니다"
  exit 0
fi

printf '%s\n' "$CRON_LINE" >>"$TMP_CRON"
crontab "$TMP_CRON"

echo "✓ dev 웹 watchdog cron 등록 완료"
echo "  line: $CRON_LINE"
