#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

ACTIVE="prod"
BACKEND_DEPLOY_LABEL="운영 API"

export ACTIVE BACKEND_DEPLOY_LABEL

exec "$SCRIPT_DIR/deploy-test-backend.sh" "${1:-$(cd "$SCRIPT_DIR/.." && pwd)}"
