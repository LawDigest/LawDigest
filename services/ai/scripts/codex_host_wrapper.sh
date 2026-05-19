#!/usr/bin/env bash

set -euo pipefail

HOST_NVM_DIR="${HOST_NVM_DIR:-/opt/host-home/.nvm}"
HOST_CODEX_HOME="${HOST_CODEX_HOME:-/opt/host-home/.codex}"
TMP_ROOT="${TMPDIR:-/tmp}"

if [ ! -d "$HOST_NVM_DIR" ]; then
  echo "HOST_NVM_DIR not found: $HOST_NVM_DIR" >&2
  exit 1
fi

if [ ! -d "$HOST_CODEX_HOME" ]; then
  echo "HOST_CODEX_HOME not found: $HOST_CODEX_HOME" >&2
  exit 1
fi

LATEST_NODE_BIN="$(find "$HOST_NVM_DIR/versions/node" -path '*/bin/node' | sort | tail -n 1)"
LATEST_CODEX_BIN="$(find "$HOST_NVM_DIR/versions/node" -path '*/bin/codex' | sort | tail -n 1)"
LATEST_CODEX_JS="$(find "$HOST_NVM_DIR/versions/node" -path '*/lib/node_modules/@openai/codex/bin/codex.js' | sort | tail -n 1)"

if [ -n "$LATEST_CODEX_BIN" ] && [ -x "$LATEST_CODEX_BIN" ]; then
  RESOLVED_CODEX_BIN="$(readlink -f "$LATEST_CODEX_BIN")"
  if [ -n "$RESOLVED_CODEX_BIN" ] && [ -f "$RESOLVED_CODEX_BIN" ]; then
    LATEST_CODEX_JS="$RESOLVED_CODEX_BIN"
  fi
fi

if [ -z "$LATEST_NODE_BIN" ] || [ ! -x "$LATEST_NODE_BIN" ]; then
  echo "Host node binary not found or not executable under $HOST_NVM_DIR" >&2
  exit 1
fi

if [ -z "$LATEST_CODEX_JS" ] || [ ! -f "$LATEST_CODEX_JS" ]; then
  echo "Host Codex CLI entrypoint not found under $HOST_NVM_DIR" >&2
  exit 1
fi

RUN_HOME="$(mktemp -d "$TMP_ROOT/codex-home.XXXXXX")"
trap 'rm -rf "$RUN_HOME"' EXIT

mkdir -p "$RUN_HOME/.codex"
for item in config.toml .credentials.json auth.json mcp.json AGENTS.md RTK.md; do
  if [ -e "$HOST_CODEX_HOME/$item" ]; then
    cp -a "$HOST_CODEX_HOME/$item" "$RUN_HOME/.codex/"
  fi
done

export HOME="$RUN_HOME"
export CODEX_HOME="$RUN_HOME/.codex"
exec "$LATEST_NODE_BIN" "$LATEST_CODEX_JS" "$@"
