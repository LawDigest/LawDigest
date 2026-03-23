#!/bin/bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WEB_DIR="$ROOT_DIR/services/web"
PORT="${PORT:-3011}"
APP_HOST="${APP_HOST:-0.0.0.0}"
PM2_NAME="${PM2_NAME:-lawdigest-web-preview}"
NEXT_PUBLIC_URL="${NEXT_PUBLIC_URL:-https://api.lawdigest.net/}"
NEXT_PUBLIC_IMAGE_URL="${NEXT_PUBLIC_IMAGE_URL:-https://api.lawdigest.net}"
NEXT_PUBLIC_HOSTNAME="${NEXT_PUBLIC_HOSTNAME:-api.lawdigest.net}"
NEXT_PUBLIC_DOMAIN="${NEXT_PUBLIC_DOMAIN:-http://127.0.0.1:$PORT}"

if [ -f "$ROOT_DIR/.env.preview" ]; then
  # shellcheck disable=SC1090
  . "$ROOT_DIR/.env.preview"
fi

echo "▶ Preview web deploy"
echo "  root: $ROOT_DIR"
echo "  branch: $(git -C "$ROOT_DIR" branch --show-current)"
echo "  commit: $(git -C "$ROOT_DIR" rev-parse --short HEAD)"
echo "  pm2: $PM2_NAME"
echo "  port: $PORT"
echo "  api: $NEXT_PUBLIC_URL"
echo "  host: $APP_HOST"
echo "  domain: $NEXT_PUBLIC_DOMAIN"

cd "$WEB_DIR"

echo "▶ npm install"
npm install

echo "▶ npm run build"
NEXT_PUBLIC_URL="$NEXT_PUBLIC_URL" NEXT_PUBLIC_IMAGE_URL="$NEXT_PUBLIC_IMAGE_URL" NEXT_PUBLIC_HOSTNAME="$NEXT_PUBLIC_HOSTNAME" NEXT_PUBLIC_DOMAIN="$NEXT_PUBLIC_DOMAIN" npm run build

if pm2 describe "$PM2_NAME" > /dev/null 2>&1; then
  echo "▶ replacing existing pm2 process: $PM2_NAME"
  pm2 delete "$PM2_NAME"
fi

echo "▶ starting preview process"
PORT="$PORT" HOSTNAME="$APP_HOST" NEXT_PUBLIC_URL="$NEXT_PUBLIC_URL" NEXT_PUBLIC_IMAGE_URL="$NEXT_PUBLIC_IMAGE_URL" NEXT_PUBLIC_HOSTNAME="$NEXT_PUBLIC_HOSTNAME" NEXT_PUBLIC_DOMAIN="$NEXT_PUBLIC_DOMAIN" pm2 start npm --name "$PM2_NAME" -- run start
pm2 save

echo "✓ Preview deployed"
echo "  url: http://$HOSTNAME:$PORT"
