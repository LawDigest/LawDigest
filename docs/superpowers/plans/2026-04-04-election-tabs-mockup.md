# 선거 탭 하위 피드/여론조사/내 지역구 목업 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 선거 탭 하위 피드/여론조사/내 지역구 3개 탭을 목업(하드코딩 모킹 데이터)으로 구현하여 UI/UX를 다듬을 수 있는 상태로 만든다.

**Architecture:** `ElectionMapShell`에 `confirmedRegion` 공유 상태를 추가하고, 각 탭을 독립 뷰 컴포넌트(`ElectionFeedView`, `ElectionPollView`, `ElectionDistrictView`)로 구현한다. 공유 컴포넌트(`PartyRingSelector`, `DistrictMapPicker`)를 먼저 개발하고 각 탭 뷰에서 재사용한다. 피드/여론조사의 지역별 뷰는 별도 컴포넌트(`FeedRegionPanel`, `PollRegionPanel`)로 추출해 `ElectionDistrictView`에서도 재사용한다.

**Tech Stack:** Next.js 14, TypeScript, NextUI v2, Tailwind CSS, Chart.js + react-chartjs-2, Vitest + @testing-library/react

**Spec:** `docs/superpowers/specs/2026-04-04-election-tabs-design.md`

---

## 사전 준비: 브랜치 생성

- [ ] **브랜치 및 워크트리 생성**

```bash
git checkout main && git pull
git checkout -b feat/election-tabs-mockup/claude
```

작업 디렉토리: `services/web/app/election/`

---

## Task 1: 목업 데이터 파일 4종 생성

**Files:**
- Create: `services/web/app/election/data/mockFeedData.ts`
- Create: `services/web/app/election/data/mockDistrictData.ts`
- Create: `services/web/app/election/data/mockPollTimeseriesData.ts`
- Create: `services/web/app/election/data/mockPartyPollData.ts`

- [ ] **Step 1: mockFeedData.ts 작성**

```ts
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
```

- [ ] **Step 2: mockDistrictData.ts 작성**

```ts
// services/web/app/election/data/mockDistrictData.ts

export interface MockCandidate {
  id: string;
  name: string;
  partyName: string;
  partyColor: string;
  slogan: string;
  supportPct: number;
  career: string[];
  pledges: string[];
  imageUrl?: string;
}

export interface MockDistrict {
  regionCode: string;
  regionName: string;
  officeName: string;
  candidates: MockCandidate[];
}

export const MOCK_DISTRICT: MockDistrict = {
  regionCode: '11',
  regionName: '서울특별시',
  officeName: '서울특별시장',
  candidates: [
    {
      id: 'c1',
      name: '홍길동',
      partyName: '더불어민주당',
      partyColor: '#152484',
      slogan: '함께 만드는 서울의 미래',
      supportPct: 47.3,
      career: ['전 서울시 경제부시장', '전 국회의원 (19대)', '서울대학교 경제학과 졸업'],
      pledges: ['청년 공공임대주택 5만 호 공급', '대중교통 요금 동결', '소상공인 임대료 안정 지원'],
    },
    {
      id: 'c2',
      name: '이순신',
      partyName: '국민의힘',
      partyColor: '#C9151E',
      slogan: '강한 서울, 행복한 시민',
      supportPct: 43.1,
      career: ['전 행정안전부 장관', '전 서울시 행정1부시장', '연세대학교 행정학과 졸업'],
      pledges: ['서울 경제 활성화 3대 프로젝트', '안전한 서울 만들기', '서울형 돌봄 서비스 확대'],
    },
    {
      id: 'c3',
      name: '강감찬',
      partyName: '조국혁신당',
      partyColor: '#6A3FA0',
      slogan: '새로운 서울의 시작',
      supportPct: 7.2,
      career: ['전 시민단체 대표', '전 서울시의원 (3선)', '고려대학교 법학과 졸업'],
      pledges: ['투명한 서울시정 실현', '기후위기 대응 그린 뉴딜', '교육 격차 해소 프로그램'],
    },
  ],
};
```

- [ ] **Step 3: mockPollTimeseriesData.ts 작성**

```ts
// services/web/app/election/data/mockPollTimeseriesData.ts

export interface PollTimeseriesPoint {
  date: string;         // 'YYYY-MM-DD'
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
  { date: dateStr(8),  더불어민주당: 47.0, 국민의힘: 43.0, 조국혁신당: 6.5, 기타: 3.5 },
  { date: dateStr(5),  더불어민주당: 47.2, 국민의힘: 43.2, 조국혁신당: 6.4, 기타: 3.2 },
  { date: dateStr(2),  더불어민주당: 47.3, 국민의힘: 43.1, 조국혁신당: 6.6, 기타: 3.0 },
  { date: dateStr(0),  더불어민주당: 47.5, 국민의힘: 42.8, 조국혁신당: 6.7, 기타: 3.0 },
];
```

- [ ] **Step 4: mockPartyPollData.ts 작성**

```ts
// services/web/app/election/data/mockPartyPollData.ts

export interface PartyPollResult {
  partyName: string;
  color: string;
  nationalPct: number;        // 전국 지지율
  regionalPct: Record<string, number>; // 시/도별 지지율
}

export const MOCK_PARTY_POLL_DATA: PartyPollResult[] = [
  {
    partyName: '더불어민주당',
    color: '#152484',
    nationalPct: 47.5,
    regionalPct: {
      서울특별시: 47.3, 경기도: 50.2, 인천광역시: 44.8,
      광주광역시: 74.8, 전북특별자치도: 71.5, 전라남도: 72.3,
      부산광역시: 39.4, 대구광역시: 35.2, 경상남도: 36.7, 경상북도: 29.8,
      대전광역시: 46.1, 세종특별자치시: 44.2, 충청북도: 42.5, 충청남도: 41.3,
      울산광역시: 40.1, 강원특별자치도: 41.2, 제주특별자치도: 52.1,
    },
  },
  {
    partyName: '국민의힘',
    color: '#C9151E',
    nationalPct: 42.8,
    regionalPct: {
      서울특별시: 43.1, 경기도: 40.5, 인천광역시: 46.5,
      광주광역시: 16.3, 전북특별자치도: 19.2, 전라남도: 18.1,
      부산광역시: 52.8, 대구광역시: 56.8, 경상남도: 55.2, 경상북도: 62.1,
      대전광역시: 44.8, 세종특별자치시: 47.3, 충청북도: 49.1, 충청남도: 50.2,
      울산광역시: 51.3, 강원특별자치도: 50.6, 제주특별자치도: 39.4,
    },
  },
  {
    partyName: '조국혁신당',
    color: '#6A3FA0',
    nationalPct: 6.7,
    regionalPct: {
      서울특별시: 7.2, 경기도: 6.8, 인천광역시: 6.5,
      광주광역시: 5.8, 전북특별자치도: 6.1, 전라남도: 6.0,
      부산광역시: 5.9, 대구광역시: 5.5, 경상남도: 5.7, 경상북도: 5.3,
      대전광역시: 6.3, 세종특별자치시: 6.0, 충청북도: 6.0, 충청남도: 5.9,
      울산광역시: 5.8, 강원특별자치도: 6.1, 제주특별자치도: 6.5,
    },
  },
];
```

- [ ] **Step 5: 커밋**

```bash
git add services/web/app/election/data/
git commit -m "feat: 선거 탭 목업 데이터 파일 4종 추가"
```

---

## Task 2: PartyRingSelector 공유 컴포넌트

**Files:**
- Create: `services/web/app/election/components/shared/PartyRingSelector.tsx`
- Create: `services/web/app/election/components/shared/PartyRingSelector.test.tsx`

- [ ] **Step 1: 실패 테스트 작성**

```tsx
// services/web/app/election/components/shared/PartyRingSelector.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import PartyRingSelector from './PartyRingSelector';

const PARTIES = [
  { name: '더불어민주당', color: '#152484' },
  { name: '국민의힘', color: '#C9151E' },
];

describe('PartyRingSelector', () => {
  it('정당 목록을 렌더링한다', () => {
    render(<PartyRingSelector parties={PARTIES} selected={null} onSelect={vi.fn()} />);
    expect(screen.getByText('더불어민주당')).toBeInTheDocument();
    expect(screen.getByText('국민의힘')).toBeInTheDocument();
  });

  it('선택 시 onSelect를 호출한다', () => {
    const onSelect = vi.fn();
    render(<PartyRingSelector parties={PARTIES} selected={null} onSelect={onSelect} />);
    fireEvent.click(screen.getByText('더불어민주당'));
    expect(onSelect).toHaveBeenCalledWith('더불어민주당');
  });

  it('이미 선택된 정당을 다시 클릭하면 null을 전달한다', () => {
    const onSelect = vi.fn();
    render(<PartyRingSelector parties={PARTIES} selected="더불어민주당" onSelect={onSelect} />);
    fireEvent.click(screen.getByText('더불어민주당'));
    expect(onSelect).toHaveBeenCalledWith(null);
  });
});
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
cd services/web && npx vitest run app/election/components/shared/PartyRingSelector.test.tsx
```
예상: FAIL (모듈 없음)

- [ ] **Step 3: 컴포넌트 구현**

```tsx
// services/web/app/election/components/shared/PartyRingSelector.tsx
'use client';

import PartyLogoReplacement from '@/components/common/PartyLogoReplacement/PartyLogoReplacement';

export interface Party {
  name: string;
  color: string;
}

interface PartyRingSelectorProps {
  parties: Party[];
  selected: string | null;
  onSelect: (partyName: string | null) => void;
}

export default function PartyRingSelector({ parties, selected, onSelect }: PartyRingSelectorProps) {
  return (
    <div className="flex gap-4 overflow-x-auto px-4 py-3 scrollbar-hide">
      {parties.map((party) => {
        const isSelected = selected === party.name;
        return (
          <button
            key={party.name}
            type="button"
            aria-pressed={isSelected}
            onClick={() => onSelect(isSelected ? null : party.name)}
            className="flex flex-col items-center gap-1.5 flex-shrink-0">
            <div
              className="rounded-full p-0.5 transition-all"
              style={{ boxShadow: isSelected ? `0 0 0 2.5px ${party.color}` : 'none' }}>
              <PartyLogoReplacement partyName={party.name} circle />
            </div>
            <span
              className={`text-[11px] max-w-[56px] text-center leading-tight transition-colors ${
                isSelected ? 'font-semibold text-gray-4 dark:text-white' : 'text-gray-2 dark:text-gray-2'
              }`}>
              {party.name}
            </span>
          </button>
        );
      })}
    </div>
  );
}
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
cd services/web && npx vitest run app/election/components/shared/PartyRingSelector.test.tsx
```
예상: PASS

- [ ] **Step 5: 커밋**

```bash
git add services/web/app/election/components/shared/
git commit -m "feat: PartyRingSelector 공유 컴포넌트 추가"
```

---

## Task 3: DistrictMapPicker 공유 컴포넌트

**Files:**
- Create: `services/web/app/election/components/shared/DistrictMapPicker.tsx`
- Create: `services/web/app/election/components/shared/DistrictMapPicker.test.tsx`

> 목업 단계: `ManualRegionPicker`를 래핑해서 시/도 단위 선택 UI를 노출한다. 선택 완료 시 접힘(collapsed) 상태로 전환하고 선택된 지역 칩을 표시한다.

- [ ] **Step 1: 실패 테스트 작성**

```tsx
// services/web/app/election/components/shared/DistrictMapPicker.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import DistrictMapPicker from './DistrictMapPicker';

vi.mock('../ManualRegionPicker', () => ({
  default: ({ onSubmit }: { onSubmit: (v: { regionCode: string; regionName: string }) => void }) => (
    <button onClick={() => onSubmit({ regionCode: '11', regionName: '서울특별시', regionType: 'PROVINCE' })}>
      서울특별시 선택
    </button>
  ),
}));

describe('DistrictMapPicker', () => {
  it('초기에는 지역 선택 UI를 보여준다', () => {
    render(<DistrictMapPicker selected={null} onSelect={vi.fn()} />);
    expect(screen.getByText('서울특별시 선택')).toBeInTheDocument();
  });

  it('지역 선택 시 onSelect를 호출한다', () => {
    const onSelect = vi.fn();
    render(<DistrictMapPicker selected={null} onSelect={onSelect} />);
    fireEvent.click(screen.getByText('서울특별시 선택'));
    expect(onSelect).toHaveBeenCalledWith({ regionCode: '11', regionName: '서울특별시' });
  });

  it('선택된 지역이 있으면 칩으로 표시하고 지도를 접는다', () => {
    render(<DistrictMapPicker selected={{ regionCode: '11', regionName: '서울특별시' }} onSelect={vi.fn()} />);
    expect(screen.getByText('서울특별시')).toBeInTheDocument();
    expect(screen.queryByText('서울특별시 선택')).not.toBeInTheDocument();
  });
});
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
cd services/web && npx vitest run app/election/components/shared/DistrictMapPicker.test.tsx
```
예상: FAIL

- [ ] **Step 3: 컴포넌트 구현**

```tsx
// services/web/app/election/components/shared/DistrictMapPicker.tsx
'use client';

import ManualRegionPicker, { ManualRegionFormValue } from '../ManualRegionPicker';

export interface SelectedRegion {
  regionCode: string;
  regionName: string;
}

interface DistrictMapPickerProps {
  selected: SelectedRegion | null;
  onSelect: (region: SelectedRegion | null) => void;  // null 허용: 선택 초기화용
  label?: string;
}

export default function DistrictMapPicker({ selected, onSelect, label = '지역 선택' }: DistrictMapPickerProps) {
  function handleSubmit(value: ManualRegionFormValue) {
    onSelect({ regionCode: value.regionCode, regionName: value.regionName });
  }

  if (selected) {
    return (
      <div className="flex items-center gap-2 px-4 py-2">
        <span className="inline-flex items-center gap-1.5 rounded-full bg-default-100 dark:bg-dark-pb px-3 py-1 text-sm font-medium text-gray-4 dark:text-white">
          📍 {selected.regionName}
        </span>
        <button
          type="button"
          onClick={() => onSelect(null)}  // null로 초기화: 빈 문자열 대신
          className="text-xs text-gray-2 hover:text-gray-3 dark:hover:text-gray-1 underline">
          변경
        </button>
      </div>
    );
  }

  return (
    <div className="px-4 py-2">
      <p className="mb-2 text-sm text-gray-2 dark:text-gray-2">{label}</p>
      <ManualRegionPicker onSubmit={handleSubmit} onCancel={() => {}} />
    </div>
  );
}
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
cd services/web && npx vitest run app/election/components/shared/DistrictMapPicker.test.tsx
```
예상: PASS

- [ ] **Step 5: 커밋**

```bash
git add services/web/app/election/components/shared/DistrictMapPicker.tsx \
        services/web/app/election/components/shared/DistrictMapPicker.test.tsx
git commit -m "feat: DistrictMapPicker 공유 컴포넌트 추가 (ManualRegionPicker 래핑)"
```

---

## Task 4: ElectionMapShell에 confirmedRegion 상태 추가

**Files:**
- Modify: `services/web/app/election/components/ElectionMapShell.tsx`

- [ ] **Step 1: ConfirmedRegion 타입 및 상태 추가 + 3개 뷰 스텁 파일 생성**

먼저 빌드가 깨지지 않도록 **스텁 파일 3개**를 만든다:

```tsx
// services/web/app/election/components/ElectionFeedView.tsx (스텁)
'use client';
import { ConfirmedRegion } from './ElectionMapShell';
export default function ElectionFeedView(_: { confirmedRegion: ConfirmedRegion | null }) {
  return <div className="p-8 text-center text-sm text-gray-2">피드 탭 구현 중...</div>;
}
```

```tsx
// services/web/app/election/components/ElectionPollView.tsx (스텁)
'use client';
import { ConfirmedRegion } from './ElectionMapShell';
export default function ElectionPollView(_: { confirmedRegion: ConfirmedRegion | null }) {
  return <div className="p-8 text-center text-sm text-gray-2">여론조사 탭 구현 중...</div>;
}
```

```tsx
// services/web/app/election/components/ElectionDistrictView.tsx (스텁)
'use client';
import { ConfirmedRegion } from './ElectionMapShell';
export default function ElectionDistrictView(_: { confirmedRegion: ConfirmedRegion | null; onRegionChange: (r: ConfirmedRegion) => void }) {
  return <div className="p-8 text-center text-sm text-gray-2">내 지역구 탭 구현 중...</div>;
}
```

그 다음 `ElectionMapShell.tsx`를 수정한다:

```tsx
'use client';

import { useState } from 'react';
import { Layout } from '@/components';
import ElectionDdayHeader from './ElectionDdayHeader';
import ElectionInnerTabBar, { ElectionInnerTab } from './ElectionInnerTabBar';
import ElectionMapTabView from './ElectionMapTabView';
import ElectionFeedView from './ElectionFeedView';
import ElectionPollView from './ElectionPollView';
import ElectionDistrictView from './ElectionDistrictView';

const LOCAL_ELECTION_DATE = new Date('2026-06-03');
const LOCAL_ELECTION_NAME = '제9회 전국동시지방선거';

export interface ConfirmedRegion {
  regionCode: string;  // e.g. '11'
  regionName: string;  // e.g. '서울특별시'
}

const DEFAULT_REGION: ConfirmedRegion = { regionCode: '11', regionName: '서울특별시' };

export default function ElectionMapShell() {
  const [activeTab, setActiveTab] = useState<ElectionInnerTab>('map');
  const [confirmedRegion, setConfirmedRegion] = useState<ConfirmedRegion | null>(DEFAULT_REGION);

  return (
    <Layout nav logo>
      <div className="flex flex-col w-full md:max-w-[768px] mx-auto">
        <ElectionDdayHeader electionName={LOCAL_ELECTION_NAME} electionDate={LOCAL_ELECTION_DATE} />
        <ElectionInnerTabBar activeTab={activeTab} onChange={setActiveTab} />

        {activeTab === 'map' && <ElectionMapTabView />}
        {activeTab === 'feed' && <ElectionFeedView confirmedRegion={confirmedRegion} />}
        {activeTab === 'poll' && <ElectionPollView confirmedRegion={confirmedRegion} />}
        {activeTab === 'district' && (
          <ElectionDistrictView confirmedRegion={confirmedRegion} onRegionChange={setConfirmedRegion} />
        )}
      </div>
    </Layout>
  );
}
```

- [ ] **Step 2: 빌드 확인 후 커밋**

```bash
cd services/web && npm run build 2>&1 | tail -10
```
예상: 빌드 성공 (스텁 파일로 인해 import 오류 없음)

```bash
git add services/web/app/election/components/ElectionMapShell.tsx \
        services/web/app/election/components/ElectionFeedView.tsx \
        services/web/app/election/components/ElectionPollView.tsx \
        services/web/app/election/components/ElectionDistrictView.tsx
git commit -m "feat: ElectionMapShell에 confirmedRegion 공유 상태 추가 + 뷰 스텁 생성"
```

---

## Task 5: BillMiniCard 컴포넌트

**Files:**
- Create: `services/web/app/election/components/BillMiniCard.tsx`
- Create: `services/web/app/election/components/BillMiniCard.test.tsx`

- [ ] **Step 1: 실패 테스트 작성**

```tsx
// services/web/app/election/components/BillMiniCard.test.tsx
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import BillMiniCard from './BillMiniCard';

describe('BillMiniCard', () => {
  const props = {
    briefSummary: '청년 주거 안정을 위한 공공임대주택 확대 법안',
    billName: '공공주택 특별법 일부개정법률안',
    billStage: '위원회 심사',
    proposeDate: '2026-03-15',
    partyName: '더불어민주당',
  };

  it('briefSummary를 렌더링한다', () => {
    render(<BillMiniCard {...props} />);
    expect(screen.getByText(props.briefSummary)).toBeInTheDocument();
  });

  it('billStage 칩을 렌더링한다', () => {
    render(<BillMiniCard {...props} />);
    expect(screen.getByText('위원회 심사')).toBeInTheDocument();
  });

  it('법안 뱃지를 렌더링한다', () => {
    render(<BillMiniCard {...props} />);
    expect(screen.getByText('법안')).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
cd services/web && npx vitest run app/election/components/BillMiniCard.test.tsx
```

- [ ] **Step 3: BillMiniCard 구현**

```tsx
// services/web/app/election/components/BillMiniCard.tsx
'use client';

import { Chip } from '@nextui-org/react';
import { BillMiniCardProps } from '../data/mockFeedData';

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' });
}

export default function BillMiniCard({ briefSummary, billName, billStage, proposeDate }: Omit<BillMiniCardProps, 'type' | 'id' | 'partyName'>) {
  return (
    <div className="rounded-2xl border border-gray-1 dark:border-dark-l bg-white dark:bg-dark-pb p-4 space-y-2">
      <div className="flex items-center gap-2">
        <span className="text-[10px] font-semibold rounded-full bg-default-100 dark:bg-dark-b px-2 py-0.5 text-gray-3 dark:text-gray-1">
          법안
        </span>
        <Chip size="sm" variant="bordered" className="text-[10px]">{billStage}</Chip>
        <span className="ml-auto text-[11px] text-gray-2">{formatDate(proposeDate)}</span>
      </div>
      <p className="text-sm font-semibold text-gray-4 dark:text-white leading-snug">{briefSummary}</p>
      <p className="text-[11px] text-gray-2 leading-snug">{billName}</p>
    </div>
  );
}
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
cd services/web && npx vitest run app/election/components/BillMiniCard.test.tsx
```

- [ ] **Step 5: 커밋**

```bash
git add services/web/app/election/components/BillMiniCard.tsx \
        services/web/app/election/components/BillMiniCard.test.tsx
git commit -m "feat: BillMiniCard 경량 법안 카드 컴포넌트 추가"
```

---

## Task 6: ElectionFeedCardList + FeedRegionPanel + PollRegionPanel 서브컴포넌트

**Files:**
- Create: `services/web/app/election/components/ElectionFeedCardList.tsx`
- Create: `services/web/app/election/components/FeedRegionPanel.tsx`
- Create: `services/web/app/election/components/PollRegionPanel.tsx`

> **순서 중요:** `FeedRegionPanel`이 `ElectionFeedCardList`를 import하므로, `ElectionFeedCardList`를 **먼저** 만든다.

- [ ] **Step 1: ElectionFeedCardList 구현 (FeedRegionPanel보다 먼저)**

Task 7에서 `ElectionFeedView`가 이 컴포넌트를 재사용하므로 여기서 먼저 작성한다.

```tsx
// services/web/app/election/components/ElectionFeedCardList.tsx
'use client';

import { FeedItem, SnsFeedItem, PollFeedItem, BillMiniCardProps } from '../data/mockFeedData';
import BillMiniCard from './BillMiniCard';

const PLATFORM_LABEL: Record<string, string> = {
  twitter: 'X', facebook: 'Facebook', instagram: 'Instagram', youtube: 'YouTube',
};

function SnsCard({ item }: { item: SnsFeedItem }) {
  const timeLabel = new Date(item.publishedAt).toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' });
  return (
    <div className="rounded-2xl border border-gray-1 dark:border-dark-l bg-white dark:bg-dark-pb p-4 space-y-2">
      <div className="flex items-center gap-2">
        <span className="text-[10px] font-semibold rounded-full bg-default-100 dark:bg-dark-b px-2 py-0.5 text-gray-3 dark:text-gray-1">
          SNS · {PLATFORM_LABEL[item.platform]}
        </span>
        <span className="text-xs text-gray-3 dark:text-gray-1 font-medium">{item.candidateName}</span>
        <span className="ml-auto text-[11px] text-gray-2">{timeLabel}</span>
      </div>
      <p className="text-sm text-gray-4 dark:text-white line-clamp-2">{item.content}</p>
      <a href={item.originalUrl} target="_blank" rel="noopener noreferrer"
        className="text-xs text-primary-2 hover:underline">원본 보기 →</a>
    </div>
  );
}

function PollCard({ item }: { item: PollFeedItem }) {
  const timeLabel = new Date(item.publishedAt).toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' });
  return (
    <div className="rounded-2xl border border-gray-1 dark:border-dark-l bg-white dark:bg-dark-pb p-4 space-y-3">
      <div className="flex items-center gap-2">
        <span className="text-[10px] font-semibold rounded-full bg-default-100 dark:bg-dark-b px-2 py-0.5 text-gray-3 dark:text-gray-1">
          여론조사
        </span>
        <span className="text-xs text-gray-3 dark:text-gray-1">{item.pollster}</span>
        <span className="ml-auto text-[11px] text-gray-2">{timeLabel}</span>
      </div>
      <div className="space-y-2">
        {item.results.map((r) => (
          <div key={r.partyName} className="flex items-center gap-2">
            <span className="text-xs text-gray-3 dark:text-gray-1 w-[80px] shrink-0">{r.partyName}</span>
            <div className="flex-1 h-2 rounded-full bg-default-100 dark:bg-dark-b overflow-hidden">
              <div className="h-full rounded-full bg-primary-2" style={{ width: `${r.pct}%` }} />
            </div>
            <span className="text-xs font-semibold text-gray-4 dark:text-white w-9 text-right">{r.pct}%</span>
            <span className={`text-[10px] w-12 text-right ${r.delta > 0 ? 'text-red-500' : r.delta < 0 ? 'text-blue-500' : 'text-gray-2'}`}>
              {r.delta > 0 ? `▲${r.delta}` : r.delta < 0 ? `▼${Math.abs(r.delta)}` : '-'}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function ElectionFeedCardList({ items }: { items: FeedItem[] }) {
  if (items.length === 0) {
    return <p className="text-center py-12 text-sm text-gray-2">아직 등록된 선거 피드가 없습니다.</p>;
  }
  return (
    <div className="space-y-3 px-4 pb-6">
      {items.map((item) => {
        if (item.type === 'sns') return <SnsCard key={item.id} item={item as SnsFeedItem} />;
        if (item.type === 'poll') return <PollCard key={item.id} item={item as PollFeedItem} />;
        if (item.type === 'bill') {
          const b = item as BillMiniCardProps;
          return <BillMiniCard key={b.id} briefSummary={b.briefSummary} billName={b.billName} billStage={b.billStage} proposeDate={b.proposeDate} />;
        }
        return null;
      })}
    </div>
  );
}
```

- [ ] **Step 2: FeedRegionPanel 구현**

```tsx
// services/web/app/election/components/FeedRegionPanel.tsx
'use client';

import { MOCK_FEED_ITEMS, FeedItem } from '../data/mockFeedData';
import ElectionFeedCardList from './ElectionFeedCardList';

interface FeedRegionPanelProps {
  region: string;
}

export default function FeedRegionPanel({ region }: FeedRegionPanelProps) {
  // bill 타입은 region 필드가 없으므로 제외하고, sns/poll만 지역 필터링
  const items: FeedItem[] = MOCK_FEED_ITEMS.filter((item) => {
    if (item.type === 'bill') return false;  // 법안은 지역 무관하므로 제외
    return (item as { region: string }).region === region;
  });

  return (
    <div className="space-y-3">
      <h3 className="px-4 text-sm font-semibold text-gray-4 dark:text-white">{region} 관련 피드</h3>
      <ElectionFeedCardList items={items.length > 0 ? items : MOCK_FEED_ITEMS.filter(i => i.type !== 'bill').slice(0, 3)} />
    </div>
  );
}
```

- [ ] **Step 2: PollRegionPanel 구현**

```tsx
// services/web/app/election/components/PollRegionPanel.tsx
'use client';

import { MOCK_POLL_DATA } from '../data/mockPollData';

interface PollRegionPanelProps {
  region: string;
}

export default function PollRegionPanel({ region }: PollRegionPanelProps) {
  const pollData = MOCK_POLL_DATA[region];

  return (
    <div className="space-y-3 px-4">
      <h3 className="text-sm font-semibold text-gray-4 dark:text-white">{region} 여론조사</h3>
      {pollData ? (
        <div className="rounded-2xl border border-gray-1 dark:border-dark-l bg-white dark:bg-dark-pb p-4 space-y-3">
          <p className="text-[11px] text-gray-2">{pollData.source}</p>
          {[
            { name: '더불어민주당', pct: pollData.c1Pct, color: '#152484' },
            { name: '국민의힘', pct: pollData.c2Pct, color: '#C9151E' },
            { name: '기타', pct: pollData.otherPct, color: '#999' },
          ].map((item) => (
            <div key={item.name} className="space-y-1">
              <div className="flex justify-between text-xs">
                <span className="text-gray-3 dark:text-gray-1">{item.name}</span>
                <span className="font-semibold text-gray-4 dark:text-white">{item.pct}%</span>
              </div>
              <div className="h-2 w-full rounded-full bg-default-100 dark:bg-dark-b overflow-hidden">
                <div className="h-full rounded-full" style={{ width: `${item.pct}%`, backgroundColor: item.color }} />
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-sm text-gray-2">해당 지역의 여론조사 결과가 없습니다.</p>
      )}
    </div>
  );
}
```

- [ ] **Step 3: 커밋**

```bash
git add services/web/app/election/components/ElectionFeedCardList.tsx \
        services/web/app/election/components/FeedRegionPanel.tsx \
        services/web/app/election/components/PollRegionPanel.tsx
git commit -m "feat: ElectionFeedCardList, FeedRegionPanel, PollRegionPanel 서브컴포넌트 추가"
```

---

## Task 7: ElectionFeedView 구현

**Files:**
- Create: `services/web/app/election/components/ElectionFeedView.tsx` (스텁 대체)
- Create: `services/web/app/election/components/ElectionFeedView.test.tsx`

- [ ] **Step 1: 실패 테스트 작성**

```tsx
// services/web/app/election/components/ElectionFeedView.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import ElectionFeedView from './ElectionFeedView';

describe('ElectionFeedView', () => {
  it('서브 뷰 탭을 렌더링한다', () => {
    render(<ElectionFeedView confirmedRegion={{ regionCode: '11', regionName: '서울특별시' }} />);
    expect(screen.getByText('전체')).toBeInTheDocument();
    expect(screen.getByText('정당별')).toBeInTheDocument();
    expect(screen.getByText('후보자별')).toBeInTheDocument();
    expect(screen.getByText('지역별')).toBeInTheDocument();
  });

  it('기본 뷰는 "전체" 탭이다', () => {
    render(<ElectionFeedView confirmedRegion={null} />);
    const allTab = screen.getByRole('tab', { name: '전체' });
    expect(allTab).toHaveAttribute('aria-selected', 'true');
  });

  it('피드 카드가 렌더링된다', () => {
    render(<ElectionFeedView confirmedRegion={null} />);
    // MOCK_FEED_ITEMS의 첫 번째 SNS 카드 내용 확인
    expect(screen.getByText(/홍길동/)).toBeInTheDocument();
  });

  it('"정당별" 탭 클릭 시 PartyRingSelector가 나타난다', () => {
    render(<ElectionFeedView confirmedRegion={null} />);
    fireEvent.click(screen.getByRole('tab', { name: '정당별' }));
    expect(screen.getByText('더불어민주당')).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
cd services/web && npx vitest run app/election/components/ElectionFeedView.test.tsx
```

- [ ] **Step 3: ElectionFeedView 구현 (스텁을 실제 구현으로 교체)**

```tsx
// services/web/app/election/components/ElectionFeedView.tsx
'use client';

import { useState } from 'react';
import { ConfirmedRegion } from './ElectionMapShell';
import { MOCK_FEED_ITEMS, FeedItem, SnsFeedItem, PollFeedItem, BillMiniCardProps } from '../data/mockFeedData';
import { MOCK_PARTY_POLL_DATA } from '../data/mockPartyPollData';
import PartyRingSelector from './shared/PartyRingSelector';
import DistrictMapPicker, { SelectedRegion } from './shared/DistrictMapPicker';
import ElectionFeedCardList from './ElectionFeedCardList';

type FeedSubView = 'all' | 'party' | 'candidate' | 'region';

const SUB_TABS: { key: FeedSubView; label: string }[] = [
  { key: 'all', label: '전체' },
  { key: 'party', label: '정당별' },
  { key: 'candidate', label: '후보자별' },
  { key: 'region', label: '지역별' },
];

const PARTIES = MOCK_PARTY_POLL_DATA.map((p) => ({ name: p.partyName, color: p.color }));

interface ElectionFeedViewProps {
  confirmedRegion: ConfirmedRegion | null;
}

export default function ElectionFeedView({ confirmedRegion }: ElectionFeedViewProps) {
  const [subView, setSubView] = useState<FeedSubView>('all');
  const [selectedParty, setSelectedParty] = useState<string | null>(null);
  const [selectedRegion, setSelectedRegion] = useState<SelectedRegion | null>(
    confirmedRegion ? { regionCode: confirmedRegion.regionCode, regionName: confirmedRegion.regionName } : null,
  );

  function filterItems(): FeedItem[] {
    if (subView === 'party' && selectedParty) {
      return MOCK_FEED_ITEMS.filter((item) => {
        if (item.type === 'sns') return (item as SnsFeedItem).partyName === selectedParty;
        if (item.type === 'poll') return (item as PollFeedItem).results.some((r) => r.partyName === selectedParty);
        if (item.type === 'bill') return (item as BillMiniCardProps).partyName === selectedParty;
        return true;
      });
    }
    if (subView === 'region' && selectedRegion?.regionName) {
      return MOCK_FEED_ITEMS.filter((item) =>
        'region' in item ? (item as SnsFeedItem | PollFeedItem).region === selectedRegion.regionName : true,
      );
    }
    return MOCK_FEED_ITEMS;
  }

  return (
    <div className="flex flex-col">
      {/* 서브 뷰 탭 */}
      <nav className="flex border-b border-gray-1 dark:border-dark-l overflow-x-auto scrollbar-hide">
        {SUB_TABS.map(({ key, label }) => {
          const isActive = key === subView;
          return (
            <button
              key={key}
              type="button"
              role="tab"
              aria-selected={isActive}
              onClick={() => setSubView(key)}
              className={[
                'relative flex-1 min-w-[72px] py-2.5 text-sm font-semibold transition-colors whitespace-nowrap',
                isActive ? 'text-gray-4 dark:text-white' : 'text-gray-2 hover:text-gray-3',
              ].join(' ')}>
              {label}
              {isActive && (
                <span className="absolute bottom-0 left-1/2 -translate-x-1/2 h-[3px] w-6 rounded-full bg-gradient-to-r from-primary-2 to-primary-3" />
              )}
            </button>
          );
        })}
      </nav>

      {/* 서브 필터 영역 */}
      {subView === 'party' && (
        <PartyRingSelector parties={PARTIES} selected={selectedParty} onSelect={setSelectedParty} />
      )}
      {(subView === 'region' || subView === 'candidate') && (
        <DistrictMapPicker
          selected={selectedRegion}
          onSelect={setSelectedRegion}
          label={subView === 'candidate' ? '후보자를 볼 지역을 선택하세요' : '지역을 선택하세요'}
        />
      )}

      {/* 피드 카드 리스트 */}
      <div className="mt-3">
        <ElectionFeedCardList items={filterItems()} />
      </div>
    </div>
  );
}
```

- [ ] **Step 5: 테스트 통과 확인**

```bash
cd services/web && npx vitest run app/election/components/ElectionFeedView.test.tsx
```
예상: PASS

- [ ] **Step 6: 커밋**

```bash
git add services/web/app/election/components/ElectionFeedView.tsx \
        services/web/app/election/components/ElectionFeedView.test.tsx
git commit -m "feat: ElectionFeedView 피드 탭 목업 구현 (전체/정당별/후보자별/지역별)"
```

---

## Task 8: ElectionPollView 구현

**Files:**
- Create: `services/web/app/election/components/ElectionPollView.tsx`
- Create: `services/web/app/election/components/ElectionPollView.test.tsx`

- [ ] **Step 1: 실패 테스트 작성**

```tsx
// services/web/app/election/components/ElectionPollView.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import ElectionPollView from './ElectionPollView';

// Chart.js는 Canvas API가 없는 jsdom에서 동작하지 않으므로 모킹
vi.mock('react-chartjs-2', () => ({
  Bar: ({ data }: { data: { labels: string[] } }) => (
    <div data-testid="bar-chart">{data.labels?.join(',')}</div>
  ),
  Line: ({ data }: { data: { labels: string[] } }) => (
    <div data-testid="line-chart">{data.labels?.join(',')}</div>
  ),
}));

describe('ElectionPollView', () => {
  it('서브 뷰 탭 4개를 렌더링한다', () => {
    render(<ElectionPollView confirmedRegion={{ regionCode: '11', regionName: '서울특별시' }} />);
    expect(screen.getByRole('tab', { name: '전체' })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: '정당별' })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: '지역별' })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: '후보자별' })).toBeInTheDocument();
  });

  it('전체 뷰에서 바차트가 렌더링된다', () => {
    render(<ElectionPollView confirmedRegion={null} />);
    expect(screen.getByTestId('bar-chart')).toBeInTheDocument();
  });

  it('"정당별" 탭 클릭 시 PartyRingSelector가 나타난다', () => {
    render(<ElectionPollView confirmedRegion={null} />);
    fireEvent.click(screen.getByRole('tab', { name: '정당별' }));
    expect(screen.getByText('더불어민주당')).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
cd services/web && npx vitest run app/election/components/ElectionPollView.test.tsx
```

- [ ] **Step 3: ElectionPollView 구현**

```tsx
// services/web/app/election/components/ElectionPollView.tsx
'use client';

import { useState } from 'react';
import { Bar, Line } from 'react-chartjs-2';
import {
  Chart as ChartJS, CategoryScale, LinearScale, BarElement,
  LineElement, PointElement, Title, Tooltip, Legend,
} from 'chart.js';
import { ConfirmedRegion } from './ElectionMapShell';
import { MOCK_POLL_DATA } from '../data/mockPollData';
import { MOCK_PARTY_POLL_DATA } from '../data/mockPartyPollData';
import { MOCK_POLL_TIMESERIES } from '../data/mockPollTimeseriesData';
import PartyRingSelector from './shared/PartyRingSelector';
import DistrictMapPicker, { SelectedRegion } from './shared/DistrictMapPicker';
import PollRegionPanel from './PollRegionPanel';

ChartJS.register(CategoryScale, LinearScale, BarElement, LineElement, PointElement, Title, Tooltip, Legend);

type PollSubView = 'all' | 'party' | 'region' | 'candidate';

const SUB_TABS: { key: PollSubView; label: string }[] = [
  { key: 'all', label: '전체' },
  { key: 'party', label: '정당별' },
  { key: 'region', label: '지역별' },
  { key: 'candidate', label: '후보자별' },
];

const PARTIES = MOCK_PARTY_POLL_DATA.map((p) => ({ name: p.partyName, color: p.color }));

interface ElectionPollViewProps {
  confirmedRegion: ConfirmedRegion | null;
}

function OverallView() {
  const barData = {
    labels: MOCK_PARTY_POLL_DATA.map((p) => p.partyName),
    datasets: [{
      label: '전국 지지율',
      data: MOCK_PARTY_POLL_DATA.map((p) => p.nationalPct),
      backgroundColor: MOCK_PARTY_POLL_DATA.map((p) => p.color),
      borderRadius: 6,
    }],
  };

  const lineData = {
    labels: MOCK_POLL_TIMESERIES.map((d) => d.date.slice(5)),
    datasets: MOCK_PARTY_POLL_DATA.map((p) => ({
      label: p.partyName,
      data: MOCK_POLL_TIMESERIES.map((d) => (d as Record<string, number>)[p.partyName] ?? 0),
      borderColor: p.color,
      backgroundColor: `${p.color}22`,
      tension: 0.4,
      pointRadius: 3,
    })),
  };

  const chartOptions = { responsive: true, plugins: { legend: { display: false } } };

  return (
    <div className="space-y-6 px-4 pb-6 pt-3">
      <div>
        <h3 className="text-sm font-semibold text-gray-4 dark:text-white mb-3">정당별 지지율</h3>
        <Bar data={barData} options={{ ...chartOptions, indexAxis: 'y' as const }} />
      </div>
      {/* TODO: 지역별 우세 정당 히트맵 — KoreaMap에 히트맵 모드 prop 추가 후 구현 (기능 구현 단계) */}
      <div>
        <h3 className="text-sm font-semibold text-gray-4 dark:text-white mb-3">지지율 추이 (최근 30일)</h3>
        <div className="flex gap-3 mb-2 flex-wrap">
          {MOCK_PARTY_POLL_DATA.map((p) => (
            <span key={p.partyName} className="flex items-center gap-1 text-[11px] text-gray-3 dark:text-gray-1">
              <span className="inline-block w-2.5 h-2.5 rounded-full" style={{ backgroundColor: p.color }} />
              {p.partyName}
            </span>
          ))}
        </div>
        <Line data={lineData} options={chartOptions} />
      </div>
      <div>
        <h3 className="text-sm font-semibold text-gray-4 dark:text-white mb-3">최신 여론조사</h3>
        {Object.entries(MOCK_POLL_DATA).slice(0, 5).map(([region, result]) => (
          <div key={region} className="rounded-xl border border-gray-1 dark:border-dark-l bg-white dark:bg-dark-pb p-3 mb-2">
            <div className="flex justify-between items-center mb-2">
              <span className="text-xs font-medium text-gray-3 dark:text-gray-1">{region}</span>
              <span className="text-[10px] text-gray-2">{result.source}</span>
            </div>
            {[
              { name: '더불어민주당', pct: result.c1Pct },
              { name: '국민의힘', pct: result.c2Pct },
            ].map((r) => (
              <div key={r.name} className="flex items-center gap-2 mb-1">
                <span className="text-[11px] text-gray-3 dark:text-gray-1 w-[80px] shrink-0">{r.name}</span>
                <div className="flex-1 h-1.5 rounded-full bg-default-100 dark:bg-dark-b overflow-hidden">
                  <div className="h-full rounded-full bg-primary-2" style={{ width: `${r.pct}%` }} />
                </div>
                <span className="text-[11px] font-semibold text-gray-4 dark:text-white">{r.pct}%</span>
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}

export default function ElectionPollView({ confirmedRegion }: ElectionPollViewProps) {
  const [subView, setSubView] = useState<PollSubView>('all');
  const [selectedParty, setSelectedParty] = useState<string | null>(null);
  const [selectedRegion, setSelectedRegion] = useState<SelectedRegion | null>(
    confirmedRegion ? { regionCode: confirmedRegion.regionCode, regionName: confirmedRegion.regionName } : null,
  );

  return (
    <div className="flex flex-col">
      {/* 서브 뷰 탭 */}
      <nav className="flex border-b border-gray-1 dark:border-dark-l overflow-x-auto scrollbar-hide">
        {SUB_TABS.map(({ key, label }) => {
          const isActive = key === subView;
          return (
            <button key={key} type="button" role="tab" aria-selected={isActive}
              onClick={() => setSubView(key)}
              className={[
                'relative flex-1 min-w-[72px] py-2.5 text-sm font-semibold transition-colors whitespace-nowrap',
                isActive ? 'text-gray-4 dark:text-white' : 'text-gray-2 hover:text-gray-3',
              ].join(' ')}>
              {label}
              {isActive && <span className="absolute bottom-0 left-1/2 -translate-x-1/2 h-[3px] w-6 rounded-full bg-gradient-to-r from-primary-2 to-primary-3" />}
            </button>
          );
        })}
      </nav>

      {subView === 'all' && <OverallView />}

      {subView === 'party' && (
        <div className="space-y-4 pb-6">
          <PartyRingSelector parties={PARTIES} selected={selectedParty} onSelect={setSelectedParty} />
          {selectedParty && (
            <div className="px-4">
              <p className="text-sm text-gray-2 text-center py-8">
                {selectedParty} 지지율 상세 데이터가 준비 중입니다.
              </p>
            </div>
          )}
          {!selectedParty && (
            <p className="text-sm text-gray-2 text-center py-8 px-4">정당을 선택해 지지율 추이를 확인하세요.</p>
          )}
        </div>
      )}

      {subView === 'region' && (
        <div className="pb-6">
          <DistrictMapPicker selected={selectedRegion} onSelect={setSelectedRegion} label="지역을 선택하세요" />
          {selectedRegion?.regionName && (
            <div className="mt-4">
              <PollRegionPanel region={selectedRegion.regionName} />
            </div>
          )}
        </div>
      )}

      {subView === 'candidate' && (
        <div className="pb-6">
          <DistrictMapPicker selected={selectedRegion} onSelect={setSelectedRegion} label="후보자를 볼 지역을 선택하세요" />
          {selectedRegion?.regionName && (
            <p className="text-sm text-gray-2 text-center py-8 px-4">
              {selectedRegion.regionName} 후보자별 지지율 추이가 준비 중입니다.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
cd services/web && npx vitest run app/election/components/ElectionPollView.test.tsx
```
예상: PASS

- [ ] **Step 5: 커밋**

```bash
git add services/web/app/election/components/ElectionPollView.tsx \
        services/web/app/election/components/ElectionPollView.test.tsx
git commit -m "feat: ElectionPollView 여론조사 탭 목업 구현 (전체/정당별/지역별/후보자별)"
```

---

## Task 9: ElectionDistrictView 구현

**Files:**
- Create: `services/web/app/election/components/ElectionDistrictView.tsx`
- Create: `services/web/app/election/components/ElectionDistrictView.test.tsx`

- [ ] **Step 1: 실패 테스트 작성**

```tsx
// services/web/app/election/components/ElectionDistrictView.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import ElectionDistrictView from './ElectionDistrictView';

vi.mock('./PollRegionPanel', () => ({
  default: ({ region }: { region: string }) => <div data-testid="poll-region-panel">{region}</div>,
}));
vi.mock('./FeedRegionPanel', () => ({
  default: ({ region }: { region: string }) => <div data-testid="feed-region-panel">{region}</div>,
}));

describe('ElectionDistrictView', () => {
  it('지역구가 설정되면 지역명을 표시한다', () => {
    render(
      <ElectionDistrictView
        confirmedRegion={{ regionCode: '11', regionName: '서울특별시' }}
        onRegionChange={vi.fn()}
      />,
    );
    expect(screen.getByText('서울특별시')).toBeInTheDocument();
  });

  it('지역구가 없으면 설정 유도 UI를 표시한다', () => {
    render(<ElectionDistrictView confirmedRegion={null} onRegionChange={vi.fn()} />);
    expect(screen.getByText('내 지역구를 설정해보세요')).toBeInTheDocument();
  });

  it('후보자 카드가 렌더링된다', () => {
    render(
      <ElectionDistrictView
        confirmedRegion={{ regionCode: '11', regionName: '서울특별시' }}
        onRegionChange={vi.fn()}
      />,
    );
    expect(screen.getByText('홍길동')).toBeInTheDocument();
  });

  it('PollRegionPanel과 FeedRegionPanel이 렌더링된다', () => {
    render(
      <ElectionDistrictView
        confirmedRegion={{ regionCode: '11', regionName: '서울특별시' }}
        onRegionChange={vi.fn()}
      />,
    );
    expect(screen.getByTestId('poll-region-panel')).toBeInTheDocument();
    expect(screen.getByTestId('feed-region-panel')).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
cd services/web && npx vitest run app/election/components/ElectionDistrictView.test.tsx
```

- [ ] **Step 3: ElectionDistrictView 구현**

```tsx
// services/web/app/election/components/ElectionDistrictView.tsx
'use client';

import { useState } from 'react';
import { ConfirmedRegion } from './ElectionMapShell';
import { MOCK_DISTRICT, MockCandidate } from '../data/mockDistrictData';
import DistrictMapPicker from './shared/DistrictMapPicker';
import PollRegionPanel from './PollRegionPanel';
import FeedRegionPanel from './FeedRegionPanel';

interface ElectionDistrictViewProps {
  confirmedRegion: ConfirmedRegion | null;
  onRegionChange: (region: ConfirmedRegion) => void;
}

function CandidateCard({ candidate, isSelected, onSelect }: {
  candidate: MockCandidate;
  isSelected: boolean;
  onSelect: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onSelect}
      className={[
        'flex flex-col items-center gap-2 p-4 rounded-2xl border transition-all min-w-[140px]',
        isSelected
          ? 'border-2 bg-default-50 dark:bg-dark-pb'
          : 'border-gray-1 dark:border-dark-l bg-white dark:bg-dark-pb',
      ].join(' ')}
      style={{ borderColor: isSelected ? candidate.partyColor : undefined }}>
      <div
        className="w-14 h-14 rounded-full flex items-center justify-center text-white font-bold text-xl"
        style={{ backgroundColor: candidate.partyColor }}>
        {candidate.name[0]}
      </div>
      <p className="text-sm font-semibold text-gray-4 dark:text-white">{candidate.name}</p>
      <p className="text-[11px] text-gray-2">{candidate.partyName}</p>
      <p className="text-[11px] text-gray-3 dark:text-gray-1 text-center leading-snug line-clamp-2">
        "{candidate.slogan}"
      </p>
      <span
        className="text-xs font-bold px-2 py-0.5 rounded-full text-white"
        style={{ backgroundColor: candidate.partyColor }}>
        {candidate.supportPct}%
      </span>
    </button>
  );
}

function CompareTable({ a, b }: { a: MockCandidate; b: MockCandidate }) {
  const rows = [
    { label: '정당', aVal: a.partyName, bVal: b.partyName },
    { label: '지지율', aVal: `${a.supportPct}%`, bVal: `${b.supportPct}%` },
    { label: '주요 공약', aVal: a.pledges[0], bVal: b.pledges[0] },
    { label: '경력', aVal: a.career[0], bVal: b.career[0] },
  ];
  return (
    <div className="mx-4 rounded-2xl border border-gray-1 dark:border-dark-l overflow-hidden">
      <div className="grid grid-cols-3 bg-default-50 dark:bg-dark-b text-[11px] font-semibold text-gray-3 dark:text-gray-1">
        <div className="p-3">항목</div>
        <div className="p-3 border-l border-gray-1 dark:border-dark-l">{a.name}</div>
        <div className="p-3 border-l border-gray-1 dark:border-dark-l">{b.name}</div>
      </div>
      {rows.map((row) => (
        <div key={row.label} className="grid grid-cols-3 border-t border-gray-1 dark:border-dark-l text-xs">
          <div className="p-3 text-gray-2 font-medium">{row.label}</div>
          <div className="p-3 border-l border-gray-1 dark:border-dark-l text-gray-4 dark:text-white">{row.aVal}</div>
          <div className="p-3 border-l border-gray-1 dark:border-dark-l text-gray-4 dark:text-white">{row.bVal}</div>
        </div>
      ))}
    </div>
  );
}

export default function ElectionDistrictView({ confirmedRegion, onRegionChange }: ElectionDistrictViewProps) {
  const [selectedCandidates, setSelectedCandidates] = useState<string[]>([]);
  const [showPicker, setShowPicker] = useState(false);

  function toggleCandidate(id: string) {
    setSelectedCandidates((prev) =>
      prev.includes(id) ? prev.filter((c) => c !== id) : prev.length < 2 ? [...prev, id] : [prev[1], id],
    );
  }

  const compareA = MOCK_DISTRICT.candidates.find((c) => c.id === selectedCandidates[0]);
  const compareB = MOCK_DISTRICT.candidates.find((c) => c.id === selectedCandidates[1]);

  if (!confirmedRegion || showPicker) {
    return (
      <div className="px-4 py-6 space-y-4">
        <div className="rounded-2xl border border-gray-1 dark:border-dark-l bg-white dark:bg-dark-pb p-5 space-y-4">
          <div className="text-center">
            <p className="text-base font-semibold text-gray-4 dark:text-white">내 지역구를 설정해보세요</p>
            <p className="text-sm text-gray-2 mt-1">지역구를 설정하면 후보자 비교와 여론조사를 볼 수 있어요.</p>
          </div>
          <DistrictMapPicker
            selected={null}
            onSelect={(region) => {
              if (region.regionCode) {
                onRegionChange(region);
                setShowPicker(false);
              }
            }}
          />
          <p className="text-xs text-center text-gray-2">저장하려면 로그인이 필요합니다.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col pb-10">
      {/* 지역구 헤더 */}
      <div className="flex items-center gap-2 px-4 py-3 border-b border-gray-1 dark:border-dark-l">
        <span className="text-sm font-semibold text-gray-4 dark:text-white">📍 {confirmedRegion.regionName}</span>
        <button
          type="button"
          onClick={() => setShowPicker(true)}
          className="text-xs text-gray-2 hover:text-gray-3 dark:hover:text-gray-1 underline ml-auto">
          변경
        </button>
      </div>

      {/* 후보자 비교 섹션 */}
      <div className="py-4 space-y-4">
        <div className="flex items-center justify-between px-4">
          <h3 className="text-sm font-semibold text-gray-4 dark:text-white">후보자 비교</h3>
          {selectedCandidates.length > 0 && (
            <p className="text-[11px] text-gray-2">{selectedCandidates.length}/2명 선택됨</p>
          )}
        </div>
        <div className="flex gap-3 overflow-x-auto px-4 scrollbar-hide pb-2">
          {MOCK_DISTRICT.candidates.map((candidate) => (
            <CandidateCard
              key={candidate.id}
              candidate={candidate}
              isSelected={selectedCandidates.includes(candidate.id)}
              onSelect={() => toggleCandidate(candidate.id)}
            />
          ))}
        </div>
        {compareA && compareB && (
          <div className="pt-2">
            <CompareTable a={compareA} b={compareB} />
          </div>
        )}
        {selectedCandidates.length < 2 && (
          <p className="text-[11px] text-center text-gray-2 px-4">후보자 2명을 선택하면 비교표가 나타납니다.</p>
        )}
      </div>

      {/* 내 지역구 여론조사 */}
      <div className="border-t border-gray-1 dark:border-dark-l pt-4">
        <PollRegionPanel region={confirmedRegion.regionName} />
      </div>

      {/* 내 지역구 피드 */}
      <div className="border-t border-gray-1 dark:border-dark-l pt-4 mt-4">
        <FeedRegionPanel region={confirmedRegion.regionName} />
      </div>
    </div>
  );
}
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
cd services/web && npx vitest run app/election/components/ElectionDistrictView.test.tsx
```
예상: PASS

- [ ] **Step 5: 커밋**

```bash
git add services/web/app/election/components/ElectionDistrictView.tsx \
        services/web/app/election/components/ElectionDistrictView.test.tsx
git commit -m "feat: ElectionDistrictView 내 지역구 탭 목업 구현"
```

---

## Task 10: index.ts 업데이트 및 전체 빌드 확인

**Files:**
- Modify: `services/web/app/election/components/index.ts`

- [ ] **Step 1: index.ts에 신규 export 추가**

`services/web/app/election/components/index.ts`에 아래 라인들을 추가한다:

```ts
export { default as ElectionFeedView } from './ElectionFeedView';
export { default as ElectionPollView } from './ElectionPollView';
export { default as ElectionDistrictView } from './ElectionDistrictView';
export { default as PollRegionPanel } from './PollRegionPanel';
export { default as FeedRegionPanel } from './FeedRegionPanel';
export { default as BillMiniCard } from './BillMiniCard';
export { default as ElectionFeedCardList } from './ElectionFeedCardList';
export { default as PartyRingSelector } from './shared/PartyRingSelector';
export { default as DistrictMapPicker } from './shared/DistrictMapPicker';
```

- [ ] **Step 2: 전체 빌드 확인**

```bash
cd services/web && npm run build 2>&1 | tail -30
```
예상: 빌드 성공 (오류 없음)

- [ ] **Step 3: 린트 확인**

```bash
cd services/web && npm run lint 2>&1 | tail -20
```

- [ ] **Step 4: 전체 테스트 확인**

```bash
cd services/web && npm test 2>&1 | tail -30
```
예상: 모든 테스트 PASS

- [ ] **Step 5: 최종 커밋**

```bash
git add services/web/app/election/components/index.ts
git commit -m "feat: election components index.ts에 신규 컴포넌트 export 추가"
```

---

## 마무리

- [ ] **PR 작성 여부 사용자에게 확인**

모든 Task 완료 후:
1. 전체 테스트 통과 확인
2. 빌드 성공 확인
3. 사용자에게 PR 작성 여부 질문
