// services/web/app/election/data/mockFeedData.ts

export type FeedCardType = 'sns' | 'poll' | 'bill' | 'youtube' | 'image';
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
  quoteText?: string;
  likes?: number;
  comments?: number;
  retweets?: number;
}

export interface PollFeedItem {
  type: 'poll';
  id: string;
  pollster: string;
  publishedAt: string;
  results: { partyName: string; pct: number; delta: number; color: string }[];
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
  region?: string;
}

// Alias for BillMiniCardProps with a more descriptive name
export type BillFeedItem = BillMiniCardProps;

export interface YoutubeFeedItem {
  type: 'youtube';
  id: string;
  candidateName: string;
  partyName: string;
  channelName: string;
  title: string;
  thumbnailUrl: string;
  publishedAt: string;
  likes?: number;
  comments?: number;
}

export interface ImageFeedItem {
  type: 'image';
  id: string;
  groupName: string;
  partyName: string;
  content: string;
  images: { src: string; alt: string }[];
  publishedAt: string;
}

export type FeedItem = SnsFeedItem | PollFeedItem | BillMiniCardProps | YoutubeFeedItem | ImageFeedItem;

export const MOCK_FEED_ITEMS: FeedItem[] = [
  {
    type: 'youtube',
    id: 'yt-1',
    candidateName: '홍길동',
    partyName: '더불어민주당',
    channelName: '더불어민주당 공식 채널',
    title: '타운홀 미팅 하이라이트: 도시 교통망 확충 공약 발표',
    thumbnailUrl: 'https://images.unsplash.com/photo-1529156069898-49953e39b3ac?w=800&q=80',
    publishedAt: '2026-04-03T09:00:00Z',
    likes: 1200,
    comments: 342,
  },
  {
    type: 'sns',
    id: 'sns-1',
    platform: 'twitter',
    candidateName: '이순신',
    partyName: '국민의힘',
    content:
      '데이터는 명확합니다: 우리 지역구에는 더 나은 연결이 필요합니다. 2027년까지 모든 가정에 기가급 광통신을 공급하겠습니다. #디지털미래 #지역우선',
    publishedAt: '2026-04-03T11:30:00Z',
    originalUrl: 'https://twitter.com/example',
    region: '서울특별시',
    quoteText: '"기술에 대한 투자는 사람에 대한 투자입니다." — 지역 경제포럼',
    likes: 156,
    comments: 18,
    retweets: 42,
  },
  {
    type: 'bill',
    id: 'bill-1',
    briefSummary: '청년 주거 안정을 위한 공공임대주택 확대 법안으로, 2030년까지 공공주택 50만 호 공급을 목표로 합니다.',
    billName: '공공주택 특별법 일부개정법률안',
    billStage: '위원회 심사',
    proposeDate: '2026-03-15',
    partyName: '더불어민주당',
  },
  {
    type: 'image',
    id: 'img-1',
    groupName: '국민의힘 서울시당',
    partyName: '국민의힘',
    content:
      '주말 서울 광장 그린업 프로젝트 성공적으로 마쳤습니다! 500그루 나무 식재, 함께 해주신 모든 분께 감사드립니다.',
    images: [
      {
        src: 'https://images.unsplash.com/photo-1466692476868-aef1dfb1e735?w=400&q=80',
        alt: '시민들과 함께하는 나무 심기 행사',
      },
      {
        src: 'https://images.unsplash.com/photo-1542601906990-b4d3fb778b09?w=400&q=80',
        alt: '자원봉사자들이 나무를 심고 있는 모습',
      },
    ],
    publishedAt: '2026-04-02T14:00:00Z',
  },
  {
    type: 'poll',
    id: 'poll-1',
    pollster: '한국갤럽',
    publishedAt: '2026-04-03T00:00:00Z',
    results: [
      { partyName: '더불어민주당', pct: 47.3, delta: 1.2, color: '#152484' },
      { partyName: '국민의힘', pct: 43.1, delta: -0.8, color: '#C9151E' },
      { partyName: '기타', pct: 9.6, delta: -0.4, color: '#999999' },
    ],
    region: '서울특별시',
  },
  {
    type: 'sns',
    id: 'sns-2',
    platform: 'instagram',
    candidateName: '강감찬',
    partyName: '조국혁신당',
    content: '청년 주거 문제 해결을 위한 공약을 발표했습니다. 새로운 시작을 함께 하겠습니다.',
    publishedAt: '2026-04-02T14:00:00Z',
    originalUrl: 'https://instagram.com/example',
    region: '경기도',
    likes: 89,
    comments: 12,
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
    type: 'poll',
    id: 'poll-2',
    pollster: '리얼미터',
    publishedAt: '2026-04-02T00:00:00Z',
    results: [
      { partyName: '더불어민주당', pct: 50.2, delta: 2.1, color: '#152484' },
      { partyName: '국민의힘', pct: 40.5, delta: -1.3, color: '#C9151E' },
      { partyName: '기타', pct: 9.3, delta: -0.8, color: '#999999' },
    ],
    region: '경기도',
  },
];
