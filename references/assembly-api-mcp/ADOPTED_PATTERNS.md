# Adopted Patterns for LawDigest

이 디렉토리는 `assembly-api-mcp` 저장소를 레퍼런스로 보관하기 위한 용도이며, LawDigest 런타임에서 직접 import 하지 않는다.

## 채택 범위
- 열린국회정보 API를 역할별로 조합하는 방식
- `BILL_ID -> BILL_NO -> summary/lifecycle/proposers` 보강 순서
- 목록 발견과 상세 hydrate를 분리하는 구조
- 부분 실패를 전체 실패로 전파하지 않는 수집 전략

## 주요 참고 API
- `BILLRCP`
- `nwbqublzajtcqpdae`
- `nzpltgfqabtcpsmai`
- `nzmimeepazxkubdpn`
- `BILLINFODETAIL`
- `BILLINFOPPSR`
- `BPMBILLSUMMARY`
- `ALLBILL`

## 비채택 범위
- MCP 서버 런타임
- TypeScript 구현체 자체
- 도구/프롬프트 레이어

## LawDigest 적용 원칙
- 수집은 `open.assembly only`로 재구성한다.
- 각 API 응답은 즉시 DB에 반영하고, 메모리에서 단일 완성 tuple을 오래 유지하지 않는다.
- 공개 여부는 `Bill.ingest_status`로 제어한다.
