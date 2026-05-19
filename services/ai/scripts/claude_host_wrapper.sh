#!/usr/bin/env bash

set -euo pipefail

HOST_LOCAL_DIR="${HOST_LOCAL_DIR:-/opt/host-home/.local}"
HOST_CLAUDE_HOME="${HOST_CLAUDE_HOME:-/opt/host-home/.claude}"
TMP_ROOT="${TMPDIR:-/tmp}"

if [ ! -d "$HOST_LOCAL_DIR" ]; then
  echo "HOST_LOCAL_DIR not found: $HOST_LOCAL_DIR" >&2
  exit 1
fi

if [ ! -d "$HOST_CLAUDE_HOME" ]; then
  echo "HOST_CLAUDE_HOME not found: $HOST_CLAUDE_HOME" >&2
  exit 1
fi

LATEST_CLAUDE_BIN=""
if [ -x "$HOST_LOCAL_DIR/bin/claude" ]; then
  LATEST_CLAUDE_BIN="$(readlink -f "$HOST_LOCAL_DIR/bin/claude")"
fi
if [ -z "$LATEST_CLAUDE_BIN" ]; then
  LATEST_CLAUDE_BIN="$(find "$HOST_LOCAL_DIR/share/claude/versions" -maxdepth 1 -type f -executable | sort | tail -n 1)"
fi

if [ -z "$LATEST_CLAUDE_BIN" ] || [ ! -x "$LATEST_CLAUDE_BIN" ]; then
  echo "Host Claude CLI entrypoint not found under $HOST_LOCAL_DIR" >&2
  exit 1
fi

RUN_HOME="$(mktemp -d "$TMP_ROOT/claude-home.XXXXXX")"
trap 'rm -rf "$RUN_HOME"' EXIT

mkdir -p "$RUN_HOME/.claude" "$RUN_HOME/.local/state"
cp -a "$HOST_CLAUDE_HOME/." "$RUN_HOME/.claude/"
if [ -d "$HOST_LOCAL_DIR/state/claude" ]; then
  cp -a "$HOST_LOCAL_DIR/state/claude" "$RUN_HOME/.local/state/"
fi

export HOME="$RUN_HOME"
exec "$LATEST_CLAUDE_BIN" "$@"
