import sys
import os
import pytest

# 프로젝트 루트 디렉토리의 src 폴더를 최우선으로 추가합니다.
# 워크트리 테스트가 다른 체크아웃의 설치본을 가져오지 않도록 합니다.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))


def pytest_addoption(parser):
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="실제 네트워크/DB가 필요한 통합 테스트도 실행합니다.",
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--run-integration"):
        return

    skip_integration = pytest.mark.skip(
        reason="통합 테스트는 --run-integration 플래그로만 실행합니다."
    )
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_integration)
