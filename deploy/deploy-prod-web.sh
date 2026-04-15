#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

PORT="${PORT:-3010}"
PM2_NAME="${PM2_NAME:-lawdigest-web-prod}"
RUNTIME_ROOT="${RUNTIME_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)/.runtime/prod-web}"
NEXT_PUBLIC_DOMAIN="${NEXT_PUBLIC_DOMAIN:-https://lawdigest.kr}"
DEPLOY_LABEL="${DEPLOY_LABEL:-운영}"

export PORT PM2_NAME RUNTIME_ROOT NEXT_PUBLIC_DOMAIN DEPLOY_LABEL

exec "$SCRIPT_DIR/deploy-web-release.sh" "${1:-$(cd "$SCRIPT_DIR/.." && pwd)}"
