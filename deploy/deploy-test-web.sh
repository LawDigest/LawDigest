#!/bin/bash
# 테스트 환경 프론트엔드 배포 스크립트 (개발 모드, test.lawdigest.net)
# 포트: 3010 / PM2 프로세스명: lawdigest-web

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WEB_DIR="$SCRIPT_DIR/../services/web"
PM2_NAME="lawdigest-web"
PORT=3010

echo "▶ 테스트 배포 시작 (개발 모드, 포트 $PORT)"

# 1. 최신 코드 pull
echo "▶ git pull..."
git -C "$SCRIPT_DIR/.." pull origin main

# 2. 의존성 설치
echo "▶ npm install..."
cd "$WEB_DIR"
npm install

# 3. 기존 PM2 프로세스 교체 (없으면 신규 시작)
echo "▶ PM2 재시작..."
if pm2 describe "$PM2_NAME" > /dev/null 2>&1; then
  pm2 delete "$PM2_NAME"
fi

PORT=$PORT pm2 start npm --name "$PM2_NAME" -- run dev
pm2 save

echo "✓ 배포 완료 → https://test.lawdigest.net"
