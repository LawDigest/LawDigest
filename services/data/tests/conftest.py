import sys
import os
import pytest

# 프로젝트 루트 디렉토리의 src 폴더를 sys.path에 추가
# 이를 통해 테스트 파일에서 src 패키지 내부의 모듈을 바로 임포트할 수 있습니다.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))


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
