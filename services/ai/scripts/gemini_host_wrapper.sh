#!/usr/bin/env bash

set -euo pipefail

HOST_NVM_DIR="${HOST_NVM_DIR:-/opt/host-home/.nvm}"
HOST_GEMINI_HOME="${HOST_GEMINI_HOME:-/opt/host-home/.gemini}"
TMP_ROOT="${TMPDIR:-/tmp}"

if [ ! -d "$HOST_NVM_DIR" ]; then
  echo "HOST_NVM_DIR not found: $HOST_NVM_DIR" >&2
  exit 1
fi

if [ ! -d "$HOST_GEMINI_HOME" ]; then
  echo "HOST_GEMINI_HOME not found: $HOST_GEMINI_HOME" >&2
  exit 1
fi

LATEST_NODE_BIN="$(find "$HOST_NVM_DIR/versions/node" -path '*/bin/node' | sort | tail -n 1)"
LATEST_GEMINI_JS="$(find "$HOST_NVM_DIR/versions/node" -path '*/lib/node_modules/@google/gemini-cli/dist/index.js' | sort | tail -n 1)"

if [ -z "$LATEST_NODE_BIN" ] || [ ! -x "$LATEST_NODE_BIN" ]; then
  echo "Host node binary not found or not executable under $HOST_NVM_DIR" >&2
  exit 1
fi

if [ -z "$LATEST_GEMINI_JS" ] || [ ! -f "$LATEST_GEMINI_JS" ]; then
  echo "Host Gemini CLI entrypoint not found under $HOST_NVM_DIR" >&2
  exit 1
fi

RUN_HOME="$(mktemp -d "$TMP_ROOT/gemini-home.XXXXXX")"
trap 'rm -rf "$RUN_HOME"' EXIT

mkdir -p "$RUN_HOME/.gemini"
cp -a "$HOST_GEMINI_HOME/." "$RUN_HOME/.gemini/"

export HOME="$RUN_HOME"
exec "$LATEST_NODE_BIN" "$LATEST_GEMINI_JS" "$@"
