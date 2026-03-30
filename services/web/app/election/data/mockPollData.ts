export interface PollResult {
  /** c1 후보 지지율(%) */
  c1Pct: number;
  /** c2 후보 지지율(%) */
  c2Pct: number;
  /** 기타/미정(%) */
  otherPct: number;
  /** 조사 출처 표시용 */
  source: string;
}

/** 시도 전체명 → 여론조사 결과 (제9회 전국동시지방선거 목업 데이터) */
export const MOCK_POLL_DATA: Record<string, PollResult> = {
  // 수도권
  서울특별시: { c1Pct: 47.3, c2Pct: 43.1, otherPct: 9.6, source: '한국갤럽 (목업)' },
  인천광역시: { c1Pct: 44.8, c2Pct: 46.5, otherPct: 8.7, source: '리얼미터 (목업)' },
  경기도: { c1Pct: 50.2, c2Pct: 40.5, otherPct: 9.3, source: '엠브레인 (목업)' },
  // 충청권
  대전광역시: { c1Pct: 46.1, c2Pct: 44.8, otherPct: 9.1, source: '한국갤럽 (목업)' },
  세종특별자치시: { c1Pct: 44.2, c2Pct: 47.3, otherPct: 8.5, source: '리얼미터 (목업)' },
  충청북도: { c1Pct: 42.5, c2Pct: 49.1, otherPct: 8.4, source: '엠브레인 (목업)' },
  충청남도: { c1Pct: 41.3, c2Pct: 50.2, otherPct: 8.5, source: '한국갤럽 (목업)' },
  // 호남권
  광주광역시: { c1Pct: 74.8, c2Pct: 16.3, otherPct: 8.9, source: '리얼미터 (목업)' },
  전라북도: { c1Pct: 71.5, c2Pct: 19.2, otherPct: 9.3, source: '엠브레인 (목업)' },
  전북특별자치도: { c1Pct: 71.5, c2Pct: 19.2, otherPct: 9.3, source: '엠브레인 (목업)' },
  전라남도: { c1Pct: 72.3, c2Pct: 18.1, otherPct: 9.6, source: '한국갤럽 (목업)' },
  // 대경권
  대구광역시: { c1Pct: 35.2, c2Pct: 56.8, otherPct: 8.0, source: '리얼미터 (목업)' },
  경상북도: { c1Pct: 29.8, c2Pct: 62.1, otherPct: 8.1, source: '엠브레인 (목업)' },
  // 동남권
  부산광역시: { c1Pct: 39.4, c2Pct: 52.8, otherPct: 7.8, source: '한국갤럽 (목업)' },
  울산광역시: { c1Pct: 40.1, c2Pct: 51.3, otherPct: 8.6, source: '리얼미터 (목업)' },
  경상남도: { c1Pct: 36.7, c2Pct: 55.2, otherPct: 8.1, source: '엠브레인 (목업)' },
  // 강원·제주
  강원도: { c1Pct: 41.2, c2Pct: 50.6, otherPct: 8.2, source: '한국갤럽 (목업)' },
  강원특별자치도: { c1Pct: 41.2, c2Pct: 50.6, otherPct: 8.2, source: '한국갤럽 (목업)' },
  제주특별자치도: { c1Pct: 52.1, c2Pct: 39.4, otherPct: 8.5, source: '리얼미터 (목업)' },
};
