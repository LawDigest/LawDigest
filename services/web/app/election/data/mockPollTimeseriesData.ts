// services/web/app/election/data/mockPollTimeseriesData.ts

export interface PollTimeseriesPoint {
  date: string; // 'YYYY-MM-DD'
  더불어민주당: number;
  국민의힘: number;
  조국혁신당: number;
  기타: number;
}

// 최근 30일 시계열 데이터 (목업)
const BASE_DATE = new Date('2026-04-04');

function dateStr(daysAgo: number): string {
  const d = new Date(BASE_DATE);
  d.setDate(d.getDate() - daysAgo);
  return d.toISOString().slice(0, 10);
}

export const MOCK_POLL_TIMESERIES: PollTimeseriesPoint[] = [
  { date: dateStr(29), 더불어민주당: 44.1, 국민의힘: 45.2, 조국혁신당: 5.3, 기타: 5.4 },
  { date: dateStr(26), 더불어민주당: 44.8, 국민의힘: 44.9, 조국혁신당: 5.5, 기타: 4.8 },
  { date: dateStr(23), 더불어민주당: 45.3, 국민의힘: 44.5, 조국혁신당: 5.7, 기타: 4.5 },
  { date: dateStr(20), 더불어민주당: 45.9, 국민의힘: 44.1, 조국혁신당: 5.9, 기타: 4.1 },
  { date: dateStr(17), 더불어민주당: 46.2, 국민의힘: 43.8, 조국혁신당: 6.0, 기타: 4.0 },
  { date: dateStr(14), 더불어민주당: 46.5, 국민의힘: 43.5, 조국혁신당: 6.1, 기타: 3.9 },
  { date: dateStr(11), 더불어민주당: 46.8, 국민의힘: 43.3, 조국혁신당: 6.3, 기타: 3.6 },
  { date: dateStr(8), 더불어민주당: 47.0, 국민의힘: 43.0, 조국혁신당: 6.5, 기타: 3.5 },
  { date: dateStr(5), 더불어민주당: 47.2, 국민의힘: 43.2, 조국혁신당: 6.4, 기타: 3.2 },
  { date: dateStr(2), 더불어민주당: 47.3, 국민의힘: 43.1, 조국혁신당: 6.6, 기타: 3.0 },
  { date: dateStr(0), 더불어민주당: 47.5, 국민의힘: 42.8, 조국혁신당: 6.7, 기타: 3.0 },
];
