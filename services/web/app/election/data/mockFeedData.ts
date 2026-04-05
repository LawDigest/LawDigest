// services/web/app/election/data/mockFeedData.ts

export type FeedCardType = 'sns' | 'poll' | 'bill';
export type SnsPlatform = 'facebook' | 'twitter' | 'instagram' | 'youtube';

export interface SnsFeedItem {
  type: 'sns';
  id: string;
  platform: SnsPlatform;
  candidateName: string;
  partyName: string;
  content: string;
  publishedAt: string;
  originalUrl: string;
  region: string;
}

export interface PollFeedItem {
  type: 'poll';
  id: string;
  pollster: string;
  publishedAt: string;
  results: { partyName: string; pct: number; delta: number }[];
  region: string;
}

export interface BillMiniCardProps {
  type: 'bill';
  id: string;
  briefSummary: string;
  billName: string;
  billStage: string;
  proposeDate: string;
  partyName: string;
}

export type FeedItem = SnsFeedItem | PollFeedItem | BillMiniCardProps;

export const MOCK_FEED_ITEMS: FeedItem[] = [
  {
    type: 'sns',
    id: 'sns-1',
    platform: 'twitter',
    candidateName: '홍길동',
    partyName: '더불어민주당',
    content: '서울 시민 여러분, 오늘 종로에서 뵙겠습니다. 함께 만드는 서울의 미래를 이야기합시다.',
    publishedAt: '2026-04-03T09:00:00Z',
    originalUrl: 'https://x.com/example',
    region: '서울특별시',
  },
  {
    type: 'sns',
    id: 'sns-2',
    platform: 'instagram',
    candidateName: '이순신',
    partyName: '국민의힘',
    content: '오늘도 현장에서 시민들의 목소리를 듣고 왔습니다. 강한 종로를 만들겠습니다.',
    publishedAt: '2026-04-03T11:30:00Z',
    originalUrl: 'https://instagram.com/example',
    region: '서울특별시',
  },
  {
    type: 'sns',
    id: 'sns-3',
    platform: 'facebook',
    candidateName: '강감찬',
    partyName: '조국혁신당',
    content: '청년 주거 문제 해결을 위한 공약을 발표했습니다. 새로운 시작을 함께 하겠습니다.',
    publishedAt: '2026-04-02T14:00:00Z',
    originalUrl: 'https://facebook.com/example',
    region: '경기도',
  },
  {
    type: 'sns',
    id: 'sns-4',
    platform: 'youtube',
    candidateName: '유관순',
    partyName: '개혁신당',
    content: '[영상] 교육 공약 발표 현장 - 모든 아이가 평등한 출발선에 서도록',
    publishedAt: '2026-04-01T16:00:00Z',
    originalUrl: 'https://youtube.com/example',
    region: '서울특별시',
  },
  {
    type: 'poll',
    id: 'poll-1',
    pollster: '한국갤럽',
    publishedAt: '2026-04-03T00:00:00Z',
    results: [
      { partyName: '더불어민주당', pct: 47.3, delta: 1.2 },
      { partyName: '국민의힘', pct: 43.1, delta: -0.8 },
      { partyName: '기타', pct: 9.6, delta: -0.4 },
    ],
    region: '서울특별시',
  },
  {
    type: 'poll',
    id: 'poll-2',
    pollster: '리얼미터',
    publishedAt: '2026-04-02T00:00:00Z',
    results: [
      { partyName: '더불어민주당', pct: 50.2, delta: 2.1 },
      { partyName: '국민의힘', pct: 40.5, delta: -1.3 },
      { partyName: '기타', pct: 9.3, delta: -0.8 },
    ],
    region: '경기도',
  },
  {
    type: 'poll',
    id: 'poll-3',
    pollster: '엠브레인',
    publishedAt: '2026-04-01T00:00:00Z',
    results: [
      { partyName: '더불어민주당', pct: 44.8, delta: -0.5 },
      { partyName: '국민의힘', pct: 46.5, delta: 0.9 },
      { partyName: '기타', pct: 8.7, delta: -0.4 },
    ],
    region: '인천광역시',
  },
  {
    type: 'bill',
    id: 'bill-1',
    briefSummary: '청년 주거 안정을 위한 공공임대주택 확대 법안',
    billName: '공공주택 특별법 일부개정법률안',
    billStage: '위원회 심사',
    proposeDate: '2026-03-15',
    partyName: '더불어민주당',
  },
  {
    type: 'bill',
    id: 'bill-2',
    briefSummary: '지방선거 선거운동 기간 확대 및 온라인 선거운동 허용 법안',
    billName: '공직선거법 일부개정법률안',
    billStage: '접수',
    proposeDate: '2026-03-20',
    partyName: '국민의힘',
  },
  {
    type: 'bill',
    id: 'bill-3',
    briefSummary: '지방자치단체 재정 자율성 강화를 위한 교부세 산정 방식 개선',
    billName: '지방교부세법 일부개정법률안',
    billStage: '본회의 심의',
    proposeDate: '2026-02-28',
    partyName: '조국혁신당',
  },
];
