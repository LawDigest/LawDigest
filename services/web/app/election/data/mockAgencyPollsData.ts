// services/web/app/election/data/mockAgencyPollsData.ts
// 실제 파싱된 여론조사 데이터 기반 (경기도 전체 / 제9회 전국동시지방선거)

export interface PollResultItem {
  label: string;
  pct: number;
  color?: string;
}

export interface AgencyPoll {
  id: string;
  agency: string; // 조사기관
  client: string; // 의뢰기관 (언론사 등)
  surveyPeriod: string; // 조사기간
  publishDate: string; // 발표일 (YYYY-MM-DD)
  sampleSize: number; // 표본수
  marginOfError: string; // 오차한계
  method: string; // 조사방법
  questionTitle: string;
  results: PollResultItem[];
}

// 실제 파싱 데이터: (주)리얼미터 – 리얼-오마이 경기도 지방선거 여론조사
// n=802, 등록번호 15391
const REALMETER_OHMYNEWS_MINJOO: AgencyPoll = {
  id: 'realmeter-ohmy-minjoo-2603',
  agency: '리얼미터',
  client: '오마이뉴스',
  surveyPeriod: '2026.03.10~11',
  publishDate: '2026-03-13',
  sampleSize: 802,
  marginOfError: '±3.5%p',
  method: 'ARS(무선70%+유선30%)',
  questionTitle: '경기도지사 더불어민주당 후보 지지도',
  results: [
    { label: '추미애', pct: 27.0, color: '#152484' },
    { label: '김동연', pct: 21.2, color: '#152484' },
    { label: '한준호', pct: 17.2, color: '#152484' },
    { label: '기타 인물', pct: 4.3, color: '#aaa' },
    { label: '없음/모름', pct: 30.2, color: '#ddd' },
  ],
};

// 실제 파싱 데이터: (주)리얼미터 – 오마이뉴스 경기도 지방선거 및 현안 조사
// n=806
const REALMETER_OHMYNEWS_PPP: AgencyPoll = {
  id: 'realmeter-ohmy-ppp-2603',
  agency: '리얼미터',
  client: '오마이뉴스',
  surveyPeriod: '2026.03.10~11',
  publishDate: '2026-03-13',
  sampleSize: 806,
  marginOfError: '±3.5%p',
  method: 'ARS(무선70%+유선30%)',
  questionTitle: '경기도지사 국민의힘 후보 지지도',
  results: [
    { label: '김은혜', pct: 20.3, color: '#C9151E' },
    { label: '유승민', pct: 15.7, color: '#C9151E' },
    { label: '안철수', pct: 12.4, color: '#C9151E' },
    { label: '기타 인물', pct: 4.4, color: '#aaa' },
    { label: '없음/모름', pct: 47.2, color: '#ddd' },
  ],
};

// 실제 파싱 데이터: (주)리얼미터 – 정당지지도 (오마이뉴스)
// n=806
const REALMETER_PARTY_SUPPORT: AgencyPoll = {
  id: 'realmeter-party-2603',
  agency: '리얼미터',
  client: '오마이뉴스',
  surveyPeriod: '2026.03.10~11',
  publishDate: '2026-03-13',
  sampleSize: 806,
  marginOfError: '±3.5%p',
  method: 'ARS(무선70%+유선30%)',
  questionTitle: '정당지지도 (경기도)',
  results: [
    { label: '더불어민주당', pct: 48.7, color: '#152484' },
    { label: '국민의힘', pct: 23.7, color: '#C9151E' },
    { label: '개혁신당', pct: 4.5, color: '#FF7210' },
    { label: '조국혁신당', pct: 4.1, color: '#6A3FA0' },
    { label: '진보당', pct: 1.6, color: '#D6001C' },
    { label: '기타/없음/모름', pct: 17.4, color: '#ddd' },
  ],
};

// 실제 파싱 데이터: (주)리얼미터 – 정당지지도 (리얼-오마이)
// n=802
const REALMETER_PARTY_SUPPORT_V2: AgencyPoll = {
  id: 'realmeter-party-v2-2603',
  agency: '리얼미터',
  client: '리얼-오마이',
  surveyPeriod: '2026.03.05~06',
  publishDate: '2026-03-08',
  sampleSize: 802,
  marginOfError: '±3.5%p',
  method: 'ARS(무선70%+유선30%)',
  questionTitle: '정당지지도 (경기도)',
  results: [
    { label: '더불어민주당', pct: 54.9, color: '#152484' },
    { label: '국민의힘', pct: 20.8, color: '#C9151E' },
    { label: '개혁신당', pct: 6.1, color: '#FF7210' },
    { label: '조국혁신당', pct: 3.0, color: '#6A3FA0' },
    { label: '진보당', pct: 2.1, color: '#D6001C' },
    { label: '기타/없음/모름', pct: 13.1, color: '#ddd' },
  ],
};

// 실제 파싱 데이터: 한길리서치 – 경기도지사 가상 대결
// n=802, 2025년 10월
const HANGIL_GOVERNOR_RACE: AgencyPoll = {
  id: 'hangil-governor-2510',
  agency: '한길리서치',
  client: '자체',
  surveyPeriod: '2025.10.17~19',
  publishDate: '2025-10-22',
  sampleSize: 802,
  marginOfError: '±3.5%p',
  method: 'ARS(무선100%)',
  questionTitle: '경기도지사 선거 정당별 지지도',
  results: [
    { label: '더불어민주당 후보', pct: 45.4, color: '#152484' },
    { label: '국민의힘 후보', pct: 30.3, color: '#C9151E' },
    { label: '기타후보', pct: 5.9, color: '#aaa' },
    { label: '없다/모름', pct: 18.3, color: '#ddd' },
  ],
};

// 실제 파싱 데이터: (주)리얼미터 – 이재명 대통령 국정운영 평가
// n=806
const REALMETER_PRESIDENT_APPROVAL: AgencyPoll = {
  id: 'realmeter-president-2603',
  agency: '리얼미터',
  client: '오마이뉴스',
  surveyPeriod: '2026.03.10~11',
  publishDate: '2026-03-13',
  sampleSize: 806,
  marginOfError: '±3.5%p',
  method: 'ARS(무선70%+유선30%)',
  questionTitle: '이재명 대통령 국정운영 평가 (경기도)',
  results: [
    { label: '매우 잘함', pct: 46.3, color: '#152484' },
    { label: '잘하는 편', pct: 10.0, color: '#96BCFA' },
    { label: '잘못하는 편', pct: 8.8, color: '#fca5a5' },
    { label: '매우 잘못함', pct: 27.2, color: '#C9151E' },
    { label: '잘 모름', pct: 7.7, color: '#ddd' },
  ],
};

// 실제 파싱 데이터: (주)리얼미터 – 경기도지사 도정운영 평가
// n=806
const REALMETER_GOVERNOR_APPROVAL: AgencyPoll = {
  id: 'realmeter-gov-approval-2603',
  agency: '리얼미터',
  client: '오마이뉴스',
  surveyPeriod: '2026.03.10~11',
  publishDate: '2026-03-13',
  sampleSize: 806,
  marginOfError: '±3.5%p',
  method: 'ARS(무선70%+유선30%)',
  questionTitle: '김동연 경기도지사 도정운영 평가',
  results: [
    { label: '매우 잘함', pct: 13.2, color: '#152484' },
    { label: '잘하는 편', pct: 25.5, color: '#96BCFA' },
    { label: '잘못하는 편', pct: 21.1, color: '#fca5a5' },
    { label: '매우 잘못함', pct: 18.8, color: '#C9151E' },
    { label: '잘 모름', pct: 21.4, color: '#ddd' },
  ],
};

// 전체 조사 목록 (최신순)
export const MOCK_AGENCY_POLLS: AgencyPoll[] = [
  REALMETER_PARTY_SUPPORT,
  REALMETER_OHMYNEWS_MINJOO,
  REALMETER_OHMYNEWS_PPP,
  REALMETER_PARTY_SUPPORT_V2,
  REALMETER_PRESIDENT_APPROVAL,
  REALMETER_GOVERNOR_APPROVAL,
  HANGIL_GOVERNOR_RACE,
];

// 전체 뷰 대표 지표 (최신 리얼미터 데이터 기준)
export const POLL_SUMMARY = {
  leadingParty: {
    name: '더불어민주당',
    pct: 48.7,
    change: +4.1, // vs 전월 대비 (목업)
    color: '#152484',
  },
  runnerUpParty: {
    name: '국민의힘',
    pct: 23.7,
    change: -1.3,
    color: '#C9151E',
  },
  gap: 25.0, // 1위-2위 격차
  undecided: 15.1, // 없음 + 잘 모름
  source: '리얼미터 (2026.03.13)',
  region: '경기도',
  election: '제9회 전국동시지방선거',
};
