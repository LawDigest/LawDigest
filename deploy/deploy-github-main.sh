#!/usr/bin/env bash

set -Eeuo pipefail

COMMIT_SHA="${1:-}"
DEPLOY_WEB="${2:-false}"
DEPLOY_BACKEND="${3:-false}"

REPO_ROOT="${LAWDIGEST_REPO_ROOT:-/home/ubuntu/project/Lawdigest}"
RUNTIME_ROOT="$REPO_ROOT/.runtime/github-actions"
WORKTREE_ROOT="$REPO_ROOT/.worktrees"
WORKTREE_PATH="$WORKTREE_ROOT/github-actions-${COMMIT_SHA:0:12}"
WORKTREE_MARKER="$WORKTREE_PATH/.lawdigest-github-actions-worktree"
LOCK_FILE="$RUNTIME_ROOT/production-deploy.lock"

validate_inputs() {
  if [[ ! "$COMMIT_SHA" =~ ^[0-9a-f]{40}$ ]]; then
    echo "✗ 유효한 40자리 git commit SHA가 아닙니다."
    exit 1
  fi

  for value in "$DEPLOY_WEB" "$DEPLOY_BACKEND"; do
    if [ "$value" != "true" ] && [ "$value" != "false" ]; then
      echo "✗ 배포 플래그는 true 또는 false여야 합니다: $value"
      exit 1
    fi
  done

  if [ "$DEPLOY_WEB" = "false" ] && [ "$DEPLOY_BACKEND" = "false" ]; then
    echo "✗ 배포할 서비스가 없습니다."
    exit 1
  fi

  if [ ! -d "$REPO_ROOT/.git" ]; then
    echo "✗ 서버 저장소를 찾을 수 없습니다: $REPO_ROOT"
    exit 1
  fi
}

cleanup_worktree() {
  if [ ! -e "$WORKTREE_PATH" ]; then
    return 0
  fi

  if [ ! -f "$WORKTREE_MARKER" ]; then
    echo "⚠ GitHub Actions 소유 표시가 없어 worktree를 자동 제거하지 않습니다: $WORKTREE_PATH"
    return 0
  fi

  git -C "$REPO_ROOT" worktree remove --force "$WORKTREE_PATH"
  git -C "$REPO_ROOT" worktree prune
}

prepare_node_runtime() {
  export NVM_DIR="${NVM_DIR:-$HOME/.nvm}"

  if [ ! -s "$NVM_DIR/nvm.sh" ]; then
    echo "✗ NVM을 찾을 수 없습니다: $NVM_DIR/nvm.sh"
    exit 1
  fi

  set +u
  # shellcheck disable=SC1091
  . "$NVM_DIR/nvm.sh"
  nvm use --silent 22.17.1
  set -u

  if [ "$(node --version)" != "v22.17.1" ]; then
    echo "✗ 예상한 Node.js 버전이 아닙니다: $(node --version)"
    exit 1
  fi
}

validate_inputs

mkdir -p "$RUNTIME_ROOT" "$WORKTREE_ROOT"
exec 9>"$LOCK_FILE"

echo "▶ 운영 배포 잠금 대기"
if ! flock -w 1800 9; then
  echo "✗ 30분 안에 운영 배포 잠금을 획득하지 못했습니다."
  exit 1
fi

echo "▶ origin/main 갱신"
git -C "$REPO_ROOT" fetch --prune origin main

if ! git -C "$REPO_ROOT" cat-file -e "${COMMIT_SHA}^{commit}" 2>/dev/null; then
  echo "✗ 서버 저장소에서 배포 커밋을 찾을 수 없습니다: $COMMIT_SHA"
  exit 1
fi

if ! git -C "$REPO_ROOT" merge-base --is-ancestor "$COMMIT_SHA" origin/main; then
  echo "✗ origin/main에 포함되지 않은 커밋은 운영 배포할 수 없습니다: $COMMIT_SHA"
  exit 1
fi

cleanup_worktree

echo "▶ 배포 worktree 생성"
git -C "$REPO_ROOT" worktree add --detach "$WORKTREE_PATH" "$COMMIT_SHA"
touch "$WORKTREE_MARKER"
trap cleanup_worktree EXIT

echo "  commit: $COMMIT_SHA"
echo "  web: $DEPLOY_WEB"
echo "  backend: $DEPLOY_BACKEND"
echo "  worktree: $WORKTREE_PATH"

if [ "$DEPLOY_BACKEND" = "true" ]; then
  echo "▶ 운영 백엔드 배포"
  "$WORKTREE_PATH/deploy/deploy-prod-backend.sh" "$WORKTREE_PATH"
fi

if [ "$DEPLOY_WEB" = "true" ]; then
  echo "▶ 운영 웹 배포"
  prepare_node_runtime
  "$WORKTREE_PATH/deploy/deploy-prod-web.sh" "$WORKTREE_PATH"
fi

echo "✓ GitHub Actions 운영 배포 완료"
