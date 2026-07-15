#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_ROOT="${1:-$(cd "$SCRIPT_DIR/.." && pwd)}"
COMMON_GIT_DIR="$(git -C "$TARGET_ROOT" rev-parse --git-common-dir)"
SHARED_REPO_ROOT="$(cd "$COMMON_GIT_DIR/.." && pwd)"

WEB_PORT="${WEB_PORT:-3010}"
PM2_NAME="${PM2_NAME:-lawdigest-web-prod}"
RUNTIME_ROOT="${RUNTIME_ROOT:-$SHARED_REPO_ROOT/.runtime/prod-web}"
NEXT_PUBLIC_DOMAIN="${NEXT_PUBLIC_DOMAIN:-https://lawdigest.kr}"
INTERNAL_API_ORIGIN="${INTERNAL_API_ORIGIN:-https://api.lawdigest.kr}"
DEPLOY_LABEL="${DEPLOY_LABEL:-운영}"

export WEB_PORT PM2_NAME RUNTIME_ROOT NEXT_PUBLIC_DOMAIN INTERNAL_API_ORIGIN DEPLOY_LABEL

exec "$SCRIPT_DIR/deploy-web-release.sh" "$TARGET_ROOT"
