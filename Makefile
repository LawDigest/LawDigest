.PHONY: help \
        dev-web dev-backend dev-data \
        build-web build-backend \
        install-web install-data \
        lint-web lint-data \
        test-backend test-data

help:
	@echo "LawDigest 모노레포 명령어"
	@echo ""
	@echo "  개발 서버"
	@echo "    make dev-web       Next.js 개발 서버 실행"
	@echo "    make dev-backend   Spring Boot 개발 서버 실행"
	@echo ""
	@echo "  빌드"
	@echo "    make build-web     Next.js 프로덕션 빌드"
	@echo "    make build-backend Spring Boot JAR 빌드"
	@echo ""
	@echo "  의존성 설치"
	@echo "    make install-web   npm install (web)"
	@echo "    make install-data  uv sync (data)"
	@echo ""
	@echo "  테스트"
	@echo "    make test-backend  Gradle 테스트"
	@echo "    make test-data     pytest"
	@echo ""
	@echo "  린트"
	@echo "    make lint-web      ESLint (web)"
	@echo "    make lint-data     ruff (data)"

# ── Web (Next.js) ──────────────────────────────────────────
dev-web:
	cd services/web && npm run dev

build-web:
	cd services/web && npm run build

install-web:
	cd services/web && npm install

lint-web:
	cd services/web && npm run lint

# ── Backend (Spring Boot) ──────────────────────────────────
dev-backend:
	cd services/backend && ./gradlew bootRun

build-backend:
	cd services/backend && ./gradlew build

test-backend:
	cd services/backend && ./gradlew test

# ── Data Pipeline (Python) ─────────────────────────────────
install-data:
	cd services/data && uv sync

test-data:
	cd services/data && uv run pytest

lint-data:
	cd services/data && uv run ruff check .
