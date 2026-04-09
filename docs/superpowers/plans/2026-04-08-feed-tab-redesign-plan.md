# 피드 탭 UI/레이아웃 리디자인 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 피드 탭 5종 카드(SNS/YouTube/법안/여론조사/이미지)의 시각적 통일성을 높이고, 정당 컬러 바 차트·컨텐츠 타입 칩·필터 상태 뱃지를 추가해 정보 가독성과 UX를 개선한다.

**Architecture:** 기존 `ElectionFeedCardList.tsx` 인라인 카드 함수들을 `feed/` 서브디렉터리로 분리하고, 공통 `FeedTypeChip`과 통일된 카드 껍데기(`bg-white border rounded-xl`)를 도입한다. 필터 적용 상태는 `ActiveFilterBadge`로 피드 상단에 표시한다.

**Tech Stack:** Next.js 14 App Router, React, TypeScript, Tailwind CSS, NextUI, Vitest + React Testing Library

---

## 디자인 결정 사항

### 카드 공통 구조
모든 카드 배경을 `bg-white dark:bg-dark-b`로 통일 (PollCard·BillCard의 `bg-gray-0.5` 제거).

```
┌──────────────────────────────────────┐
│ [타입 칩]  출처/제목          시간     │  ← 헤더 (항상 존재)
│                                      │
│  (카드별 본문)                        │  ← 본문
│                                      │
│ 💬 n  🔄 n  ❤️ n              [공유]  │  ← 액션 (있는 카드만)
└──────────────────────────────────────┘
```

### 타입 칩 색상표

| 타입 | 배경 | 텍스트 | 아이콘 |
|------|------|--------|--------|
| 여론조사 | `bg-red-50` | `text-red-600` | `bar_chart` |
| SNS | `bg-blue-50` | `text-blue-600` | `tag` / `photo_camera` |
| 법안 | `bg-green-50` | `text-green-700` | `gavel` |
| 영상 | `bg-purple-50` | `text-purple-600` | `play_circle` |
| 이미지 | `bg-gray-0.5` | `text-gray-3` | `image` |

### 카드별 주요 변경

| 카드 | 현재 → 개선 |
|------|-----------|
| **SNS** | 아바타 48px → 32px, 메타 2줄 → 1줄 (`이름 · 정당 · X`) |
| **YouTube** | 전체 너비 썸네일 → 좌측 140px 고정 + 우측 텍스트 (모바일은 전체 너비 유지) |
| **Poll** | 바 `bg-primary-2` (단색) → 정당 컬러 인라인 스타일, 바 두께 `h-2`→`h-3`, 장식 아이콘 제거 |
| **Bill** | `bg-gray-0.5` + 장식 gavel 제거 → `bg-white`, `BillMiniCard.tsx`와 통합 |
| **Image** | 변경 없음 (구조만 타입 칩으로 통일) |

### 필터 활성 뱃지
필터(정당/지역/후보자) 적용 중일 때 피드 상단:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  더불어민주당 필터 적용 중  [✕ 해제]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 파일 구조

### 신규 생성
```
services/web/app/election/components/feed/
├── utils.ts                  # timeAgo, formatCount 공유 유틸
├── FeedTypeChip.tsx          # 컨텐츠 타입 칩 (여론조사/SNS/법안/영상/이미지)
├── ActiveFilterBadge.tsx     # 필터 적용 상태 바 (해제 버튼 포함)
├── SnsCard.tsx               # SNS 카드 (컴팩트 레이아웃)
├── YoutubeCard.tsx           # YouTube 카드 (썸네일 좌측 고정)
├── PollCard.tsx              # 여론조사 카드 (정당 컬러 바)
├── BillCard.tsx              # 법안 카드 (BillMiniCard 통합)
├── ImageCard.tsx             # 이미지 카드
└── index.ts                  # 전체 export
```

### 수정
```
services/web/app/election/
├── components/ElectionFeedCardList.tsx   # feed/ 카드들 import로 교체
├── components/ElectionFeedView.tsx       # ActiveFilterBadge 추가
├── components/BillMiniCard.tsx           # 삭제 (BillCard로 통합)
└── data/mockFeedData.ts                  # BillMiniCardProps에 region?: string 추가
```

### 테스트
```
services/web/app/election/components/feed/
├── FeedTypeChip.test.tsx
├── SnsCard.test.tsx
├── YoutubeCard.test.tsx
├── PollCard.test.tsx
└── BillCard.test.tsx
```

---

## Task 1: feed/utils.ts — 공유 유틸 추출

**Files:**
- Create: `services/web/app/election/components/feed/utils.ts`
- Create: `services/web/app/election/components/feed/utils.test.ts`

`timeAgo`와 `formatCount`가 모든 카드에 중복되지 않도록 한 곳에 정의한다.

- [ ] **Step 1: 테스트 작성**

```typescript
// utils.test.ts
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { timeAgo, formatCount, formatDate } from './utils';

describe('timeAgo', () => {
  beforeEach(() => {
    vi.setSystemTime(new Date('2026-04-08T12:00:00Z'));
  });
  afterEach(() => {
    vi.useRealTimers();
  });

  it('1시간 이내면 분 단위로 반환한다', () => {
    expect(timeAgo('2026-04-08T11:30:00Z')).toBe('30분 전');
  });

  it('24시간 이내면 시간 단위로 반환한다', () => {
    expect(timeAgo('2026-04-08T06:00:00Z')).toBe('6시간 전');
  });

  it('24시간 이상이면 일 단위로 반환한다', () => {
    expect(timeAgo('2026-04-06T12:00:00Z')).toBe('2일 전');
  });
});

describe('formatCount', () => {
  it('undefined이면 0을 반환한다', () => {
    expect(formatCount(undefined)).toBe('0');
  });

  it('1000 미만이면 숫자 그대로 반환한다', () => {
    expect(formatCount(342)).toBe('342');
  });

  it('1000 이상이면 k 단위로 반환한다', () => {
    expect(formatCount(1200)).toBe('1.2k');
  });
});

describe('formatDate', () => {
  it('ISO 날짜 문자열을 한국어 월/일 형태로 반환한다', () => {
    expect(formatDate('2026-03-15')).toBe('3월 15일');
  });
});
```

- [ ] **Step 2: 테스트 실행 (FAIL 확인)**

```bash
cd /home/ubuntu/project/Lawdigest/services/web
npx vitest run app/election/components/feed/utils.test.ts
```

- [ ] **Step 3: utils.ts 작성**

```typescript
// utils.ts
export function timeAgo(dateStr: string): string {
  const diff = Math.floor((Date.now() - new Date(dateStr).getTime()) / 1000);
  if (diff < 3600) return `${Math.floor(diff / 60)}분 전`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}시간 전`;
  return `${Math.floor(diff / 86400)}일 전`;
}

export function formatCount(n?: number): string {
  if (!n) return '0';
  return n >= 1000 ? `${(n / 1000).toFixed(1)}k` : String(n);
}

export function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('ko-KR', { month: 'numeric', day: 'numeric' });
}
```

- [ ] **Step 4: 테스트 실행 (PASS 확인)**

```bash
cd /home/ubuntu/project/Lawdigest/services/web
npx vitest run app/election/components/feed/utils.test.ts
```

- [ ] **Step 5: 커밋**

```bash
git add services/web/app/election/components/feed/utils.ts \
        services/web/app/election/components/feed/utils.test.ts
git commit -m "feat: feed/utils.ts — timeAgo, formatCount 공유 유틸 추출"
```

---

## Task 2: FeedTypeChip 컴포넌트

**Files:**
- Create: `services/web/app/election/components/feed/FeedTypeChip.tsx`
- Create: `services/web/app/election/components/feed/FeedTypeChip.test.tsx`

- [ ] **Step 1: 테스트 작성**

```typescript
// FeedTypeChip.test.tsx
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import FeedTypeChip from './FeedTypeChip';

describe('FeedTypeChip', () => {
  it('여론조사 타입을 렌더링한다', () => {
    render(<FeedTypeChip type="poll" />);
    expect(screen.getByText('여론조사')).toBeInTheDocument();
  });

  it('SNS 타입을 렌더링한다', () => {
    render(<FeedTypeChip type="sns" platform="twitter" />);
    expect(screen.getByText('SNS')).toBeInTheDocument();
  });

  it('법안 타입을 렌더링한다', () => {
    render(<FeedTypeChip type="bill" />);
    expect(screen.getByText('법안')).toBeInTheDocument();
  });

  it('영상 타입을 렌더링한다', () => {
    render(<FeedTypeChip type="youtube" />);
    expect(screen.getByText('영상')).toBeInTheDocument();
  });

  it('이미지 타입을 렌더링한다', () => {
    render(<FeedTypeChip type="image" />);
    expect(screen.getByText('이미지')).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: 테스트 실행 (FAIL 확인)**

```bash
cd /home/ubuntu/project/Lawdigest/services/web
npx vitest run app/election/components/feed/FeedTypeChip.test.tsx
```

- [ ] **Step 3: 구현**

```typescript
// FeedTypeChip.tsx
'use client';

import { type SnsPlatform } from '../../data/mockFeedData';

type FeedType = 'poll' | 'sns' | 'bill' | 'youtube' | 'image';

interface FeedTypeChipProps {
  type: FeedType;
  platform?: SnsPlatform;
}

const CHIP_CONFIG: Record<FeedType, { label: string; icon: string; className: string }> = {
  poll:    { label: '여론조사', icon: 'bar_chart',    className: 'bg-red-50 text-red-600' },
  sns:     { label: 'SNS',    icon: 'tag',           className: 'bg-blue-50 text-blue-600' },
  bill:    { label: '법안',   icon: 'gavel',         className: 'bg-green-50 text-green-700' },
  youtube: { label: '영상',   icon: 'play_circle',   className: 'bg-purple-50 text-purple-600' },
  image:   { label: '이미지', icon: 'image',         className: 'bg-gray-0.5 text-gray-3' },
};

const PLATFORM_ICON: Record<SnsPlatform, string> = {
  twitter: 'tag', facebook: 'public', instagram: 'photo_camera', youtube: 'play_circle',
};

export default function FeedTypeChip({ type, platform }: FeedTypeChipProps) {
  const config = CHIP_CONFIG[type];
  const icon = type === 'sns' && platform ? PLATFORM_ICON[platform] : config.icon;
  return (
    <span className={`inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full ${config.className}`}>
      <span className="material-symbols-outlined text-[11px]" style={{ fontVariationSettings: "'FILL' 1" }}>
        {icon}
      </span>
      {config.label}
    </span>
  );
}
```

- [ ] **Step 4: 테스트 실행 (PASS 확인)**

```bash
cd /home/ubuntu/project/Lawdigest/services/web
npx vitest run app/election/components/feed/FeedTypeChip.test.tsx
```

- [ ] **Step 5: 커밋**

```bash
git add services/web/app/election/components/feed/FeedTypeChip.tsx \
        services/web/app/election/components/feed/FeedTypeChip.test.tsx
git commit -m "feat: FeedTypeChip 컴포넌트 추가 (여론조사/SNS/법안/영상/이미지)"
```

---

## Task 3: ActiveFilterBadge 컴포넌트

**Files:**
- Create: `services/web/app/election/components/feed/ActiveFilterBadge.tsx`
- Create: `services/web/app/election/components/feed/ActiveFilterBadge.test.tsx`

- [ ] **Step 1: 테스트 작성**

```typescript
// ActiveFilterBadge.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import ActiveFilterBadge from './ActiveFilterBadge';

describe('ActiveFilterBadge', () => {
  it('label을 렌더링한다', () => {
    render(<ActiveFilterBadge label="더불어민주당" onClear={() => {}} />);
    expect(screen.getByText('더불어민주당 필터 적용 중')).toBeInTheDocument();
  });

  it('해제 버튼 클릭 시 onClear를 호출한다', () => {
    const onClear = vi.fn();
    render(<ActiveFilterBadge label="국민의힘" onClear={onClear} />);
    fireEvent.click(screen.getByRole('button', { name: /해제/ }));
    expect(onClear).toHaveBeenCalledTimes(1);
  });
});
```

- [ ] **Step 2: 테스트 실행 (FAIL 확인)**

```bash
cd /home/ubuntu/project/Lawdigest/services/web
npx vitest run app/election/components/feed/ActiveFilterBadge.test.tsx
```

- [ ] **Step 3: 구현**

```typescript
// ActiveFilterBadge.tsx
'use client';

interface ActiveFilterBadgeProps {
  label: string;
  onClear: () => void;
}

export default function ActiveFilterBadge({ label, onClear }: ActiveFilterBadgeProps) {
  return (
    <div className="flex items-center justify-between px-4 py-2 bg-primary-1 dark:bg-dark-l/40 border-b border-gray-1 dark:border-dark-l text-xs text-gray-3 dark:text-gray-1">
      <span className="flex items-center gap-1.5">
        <span className="material-symbols-outlined text-[14px] text-primary-2">filter_alt</span>
        <span className="font-medium">{label} 필터 적용 중</span>
      </span>
      <button
        type="button"
        onClick={onClear}
        aria-label="필터 해제"
        className="flex items-center gap-0.5 text-gray-2 hover:text-gray-4 dark:hover:text-white transition-colors">
        <span className="material-symbols-outlined text-[14px]">close</span>
        해제
      </button>
    </div>
  );
}
```

- [ ] **Step 4: 테스트 실행 (PASS 확인)**

```bash
cd /home/ubuntu/project/Lawdigest/services/web
npx vitest run app/election/components/feed/ActiveFilterBadge.test.tsx
```

- [ ] **Step 5: 커밋**

```bash
git add services/web/app/election/components/feed/ActiveFilterBadge.tsx \
        services/web/app/election/components/feed/ActiveFilterBadge.test.tsx
git commit -m "feat: ActiveFilterBadge 컴포넌트 추가 (필터 적용 상태 표시 + 해제)"
```

---

## Task 4: PollCard 리디자인 (정당 컬러 바)

**Files:**
- Modify: `services/web/app/election/data/mockFeedData.ts`
- Create: `services/web/app/election/components/feed/PollCard.tsx`
- Create: `services/web/app/election/components/feed/PollCard.test.tsx`

- [ ] **Step 1: mockFeedData.ts — PollResult에 color 필드 추가 (테스트 작성 전 선행)**

`services/web/app/election/data/mockFeedData.ts`의 `PollFeedItem` 인터페이스 수정:

```typescript
export interface PollFeedItem {
  type: 'poll';
  id: string;
  pollster: string;
  publishedAt: string;
  results: { partyName: string; pct: number; delta: number; color: string }[];
  region: string;
}
```

`BillMiniCardProps`에도 `region` 필드 추가:

```typescript
export interface BillMiniCardProps {
  type: 'bill';
  id: string;
  briefSummary: string;
  billName: string;
  billStage: string;
  proposeDate: string;
  partyName: string;
  region?: string;  // 추가
}
```

`MOCK_FEED_ITEMS`의 poll 아이템 results에 `color` 값 추가:

```typescript
// poll-1
results: [
  { partyName: '더불어민주당', pct: 47.3, delta: 1.2,  color: '#152484' },
  { partyName: '국민의힘',     pct: 43.1, delta: -0.8, color: '#C9151E' },
  { partyName: '기타',         pct: 9.6,  delta: -0.4, color: '#999999' },
],
// poll-2
results: [
  { partyName: '더불어민주당', pct: 50.2, delta: 2.1,  color: '#152484' },
  { partyName: '국민의힘',     pct: 40.5, delta: -1.3, color: '#C9151E' },
  { partyName: '기타',         pct: 9.3,  delta: -0.8, color: '#999999' },
],
```

- [ ] **Step 2: 테스트 작성**

```typescript
// PollCard.test.tsx
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import PollCard from './PollCard';

const mockItem = {
  type: 'poll' as const,
  id: 'poll-1',
  pollster: '한국갤럽',
  publishedAt: '2026-04-03T00:00:00Z',
  results: [
    { partyName: '더불어민주당', pct: 47.3, delta: 1.2, color: '#152484' },
    { partyName: '국민의힘', pct: 43.1, delta: -0.8, color: '#C9151E' },
  ],
  region: '서울특별시',
};

describe('PollCard', () => {
  it('조사기관명을 렌더링한다', () => {
    render(<PollCard item={mockItem} />);
    expect(screen.getByText('한국갤럽')).toBeInTheDocument();
  });

  it('지역을 렌더링한다', () => {
    render(<PollCard item={mockItem} />);
    expect(screen.getByText('서울특별시')).toBeInTheDocument();
  });

  it('모든 정당 결과를 렌더링한다', () => {
    render(<PollCard item={mockItem} />);
    expect(screen.getByText('더불어민주당')).toBeInTheDocument();
    expect(screen.getByText('국민의힘')).toBeInTheDocument();
  });

  it('퍼센트를 렌더링한다', () => {
    render(<PollCard item={mockItem} />);
    expect(screen.getByText('47.3%')).toBeInTheDocument();
  });

  it('타입 칩을 렌더링한다', () => {
    render(<PollCard item={mockItem} />);
    expect(screen.getByText('여론조사')).toBeInTheDocument();
  });
});
```

- [ ] **Step 3: 테스트 실행 (FAIL 확인)**

```bash
cd /home/ubuntu/project/Lawdigest/services/web
npx vitest run app/election/components/feed/PollCard.test.tsx
```

- [ ] **Step 4: PollCard 구현 (utils.ts import)**

```typescript
// PollCard.tsx
'use client';

import { PollFeedItem } from '../../data/mockFeedData';
import FeedTypeChip from './FeedTypeChip';
import { timeAgo } from './utils';

function DeltaBadge({ delta }: { delta: number }) {
  if (delta > 0) return <span className="text-[10px] w-10 text-right font-medium text-blue-500">▲{delta}</span>;
  if (delta < 0) return <span className="text-[10px] w-10 text-right font-medium text-red-400">▼{Math.abs(delta)}</span>;
  return <span className="text-[10px] w-10 text-right font-medium text-gray-2">-</span>;
}

export default function PollCard({ item }: { item: PollFeedItem }) {
  const maxPct = Math.max(...item.results.map((r) => r.pct));
  return (
    <article className="bg-white dark:bg-dark-b p-4 rounded-xl border border-gray-1 dark:border-dark-l shadow-sm">
      {/* 헤더 */}
      <div className="flex items-center gap-2 mb-3">
        <FeedTypeChip type="poll" />
        <span className="text-xs font-semibold text-gray-4 dark:text-white truncate">{item.pollster}</span>
        <span className="text-[10px] text-gray-2 shrink-0">{item.region}</span>
        <span className="ml-auto text-[10px] text-gray-2 shrink-0">{timeAgo(item.publishedAt)}</span>
      </div>
      {/* 바 차트 */}
      <div className="space-y-2.5">
        {item.results.map((r) => (
          <div key={r.partyName} className="flex items-center gap-2">
            <span className="text-xs text-gray-3 dark:text-gray-1 w-[80px] shrink-0 truncate">{r.partyName}</span>
            <div className="flex-1 h-3 rounded-full bg-gray-0.5 dark:bg-dark-l overflow-hidden">
              <div
                className="h-full rounded-full animate-bar-grow origin-left"
                style={{ width: `${(r.pct / maxPct) * 100}%`, backgroundColor: r.color }}
              />
            </div>
            <span className="text-xs font-bold text-gray-4 dark:text-white w-10 text-right tabular-nums">{r.pct}%</span>
            <DeltaBadge delta={r.delta} />
          </div>
        ))}
      </div>
    </article>
  );
}
```

- [ ] **Step 5: 테스트 실행 (PASS 확인)**

```bash
cd /home/ubuntu/project/Lawdigest/services/web
npx vitest run app/election/components/feed/PollCard.test.tsx
```

- [ ] **Step 6: 커밋**

```bash
git add services/web/app/election/components/feed/PollCard.tsx \
        services/web/app/election/components/feed/PollCard.test.tsx \
        services/web/app/election/data/mockFeedData.ts
git commit -m "feat: PollCard 리디자인 — 정당 컬러 바 차트, 타입 칩, 흰 배경"
```

---

## Task 5: SnsCard 리디자인 (컴팩트 레이아웃)

**Files:**
- Create: `services/web/app/election/components/feed/SnsCard.tsx`
- Create: `services/web/app/election/components/feed/SnsCard.test.tsx`

- [ ] **Step 1: 테스트 작성**

```typescript
// SnsCard.test.tsx
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import SnsCard from './SnsCard';

const mockItem = {
  type: 'sns' as const,
  id: 'sns-1',
  platform: 'twitter' as const,
  candidateName: '이순신',
  partyName: '국민의힘',
  content: '디지털 미래를 위한 공약을 발표합니다.',
  publishedAt: '2026-04-03T11:30:00Z',
  originalUrl: 'https://twitter.com/example',
  region: '서울특별시',
  likes: 156,
  comments: 18,
  retweets: 42,
};

describe('SnsCard', () => {
  it('후보자명을 렌더링한다', () => {
    render(<SnsCard item={mockItem} />);
    expect(screen.getByText('이순신')).toBeInTheDocument();
  });

  it('정당명을 렌더링한다', () => {
    render(<SnsCard item={mockItem} />);
    expect(screen.getByText('국민의힘')).toBeInTheDocument();
  });

  it('본문 내용을 렌더링한다', () => {
    render(<SnsCard item={mockItem} />);
    expect(screen.getByText('디지털 미래를 위한 공약을 발표합니다.')).toBeInTheDocument();
  });

  it('좋아요 수를 렌더링한다', () => {
    render(<SnsCard item={mockItem} />);
    expect(screen.getByText('156')).toBeInTheDocument();
  });

  it('타입 칩을 렌더링한다', () => {
    render(<SnsCard item={mockItem} />);
    expect(screen.getByText('SNS')).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: 테스트 실행 (FAIL 확인)**

```bash
cd /home/ubuntu/project/Lawdigest/services/web
npx vitest run app/election/components/feed/SnsCard.test.tsx
```

- [ ] **Step 3: SnsCard 구현**

```typescript
// SnsCard.tsx
'use client';

import { SnsFeedItem } from '../../data/mockFeedData';
import FeedTypeChip from './FeedTypeChip';
import { timeAgo, formatCount } from './utils';

export default function SnsCard({ item }: { item: SnsFeedItem }) {
  return (
    <article className="bg-white dark:bg-dark-b p-4 rounded-xl border border-gray-1 dark:border-dark-l shadow-sm">
      {/* 헤더: 타입 칩 + 후보명 · 정당 + 시간 */}
      <div className="flex items-center gap-2 mb-3">
        <FeedTypeChip type="sns" platform={item.platform} />
        <div className="flex items-center gap-1 min-w-0 flex-1">
          <span className="text-xs font-bold text-gray-4 dark:text-white truncate">{item.candidateName}</span>
          <span className="text-[10px] text-gray-2 shrink-0">· {item.partyName}</span>
        </div>
        <span className="text-[10px] text-gray-2 shrink-0">{timeAgo(item.publishedAt)}</span>
      </div>
      {/* 본문 */}
      <p className="text-sm text-gray-4 dark:text-white leading-relaxed line-clamp-3">{item.content}</p>
      {item.quoteText && (
        <div className="mt-2 p-3 bg-gray-0.5 dark:bg-dark-l/30 rounded-lg border-l-4 border-primary-2/40">
          <p className="text-xs text-gray-2 italic line-clamp-2">{item.quoteText}</p>
        </div>
      )}
      {/* 액션 */}
      <div className="flex items-center gap-5 mt-3 pt-3 border-t border-gray-0.5 dark:border-dark-l/30 text-gray-2">
        <button type="button" className="flex items-center gap-1 hover:text-primary-2 transition-colors">
          <span className="material-symbols-outlined text-[16px]">mode_comment</span>
          <span className="text-[11px] font-medium">{formatCount(item.comments)}</span>
        </button>
        <button type="button" className="flex items-center gap-1 hover:text-gray-3 transition-colors">
          <span className="material-symbols-outlined text-[16px]">recycling</span>
          <span className="text-[11px] font-medium">{formatCount(item.retweets)}</span>
        </button>
        <button type="button" className="flex items-center gap-1 hover:text-red-400 transition-colors">
          <span className="material-symbols-outlined text-[16px]">favorite</span>
          <span className="text-[11px] font-medium">{formatCount(item.likes)}</span>
        </button>
        <button type="button" className="ml-auto text-gray-2 hover:text-gray-4 transition-colors" aria-label="공유">
          <span className="material-symbols-outlined text-[16px]">share</span>
        </button>
      </div>
    </article>
  );
}
```

- [ ] **Step 4: 테스트 실행 (PASS 확인)**

```bash
cd /home/ubuntu/project/Lawdigest/services/web
npx vitest run app/election/components/feed/SnsCard.test.tsx
```

- [ ] **Step 5: 커밋**

```bash
git add services/web/app/election/components/feed/SnsCard.tsx \
        services/web/app/election/components/feed/SnsCard.test.tsx
git commit -m "feat: SnsCard 리디자인 — 컴팩트 헤더, 타입 칩, line-clamp"
```

---

## Task 6: YoutubeCard 리디자인 (수평 레이아웃)

**Files:**
- Create: `services/web/app/election/components/feed/YoutubeCard.tsx`
- Create: `services/web/app/election/components/feed/YoutubeCard.test.tsx`

- [ ] **Step 1: 테스트 작성**

```typescript
// YoutubeCard.test.tsx
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import YoutubeCard from './YoutubeCard';

const mockItem = {
  type: 'youtube' as const,
  id: 'yt-1',
  candidateName: '홍길동',
  partyName: '더불어민주당',
  channelName: '더불어민주당 공식 채널',
  title: '타운홀 미팅 하이라이트',
  thumbnailUrl: 'https://example.com/thumb.jpg',
  publishedAt: '2026-04-03T09:00:00Z',
  likes: 1200,
  comments: 342,
};

describe('YoutubeCard', () => {
  it('영상 제목을 렌더링한다', () => {
    render(<YoutubeCard item={mockItem} />);
    expect(screen.getByText('타운홀 미팅 하이라이트')).toBeInTheDocument();
  });

  it('채널명을 렌더링한다', () => {
    render(<YoutubeCard item={mockItem} />);
    expect(screen.getByText('더불어민주당 공식 채널')).toBeInTheDocument();
  });

  it('재생 버튼에 aria-label이 있다', () => {
    render(<YoutubeCard item={mockItem} />);
    expect(screen.getByRole('button', { name: '영상 재생' })).toBeInTheDocument();
  });

  it('타입 칩을 렌더링한다', () => {
    render(<YoutubeCard item={mockItem} />);
    expect(screen.getByText('영상')).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: 테스트 실행 (FAIL 확인)**

```bash
cd /home/ubuntu/project/Lawdigest/services/web
npx vitest run app/election/components/feed/YoutubeCard.test.tsx
```

- [ ] **Step 3: YoutubeCard 구현**

```typescript
// YoutubeCard.tsx
'use client';

import Image from 'next/image';
import { YoutubeFeedItem } from '../../data/mockFeedData';
import FeedTypeChip from './FeedTypeChip';
import { timeAgo, formatCount } from './utils';

export default function YoutubeCard({ item }: { item: YoutubeFeedItem }) {
  return (
    <article className="bg-white dark:bg-dark-b p-4 rounded-xl border border-gray-1 dark:border-dark-l shadow-sm">
      {/* 헤더 */}
      <div className="flex items-center gap-2 mb-3">
        <FeedTypeChip type="youtube" />
        <span className="text-xs text-gray-2 truncate flex-1">{item.candidateName} · {item.partyName}</span>
        <span className="text-[10px] text-gray-2 shrink-0">{timeAgo(item.publishedAt)}</span>
      </div>
      {/* 수평 레이아웃: 썸네일 좌측 고정 + 우측 텍스트 */}
      <div className="flex gap-3">
        <div className="relative w-[140px] shrink-0 rounded-lg overflow-hidden aspect-video group">
          <Image src={item.thumbnailUrl} alt={item.title} fill unoptimized className="object-cover group-hover:scale-105 transition-transform duration-500" />
          <div className="absolute inset-0 bg-black/25 flex items-center justify-center">
            <button
              type="button"
              aria-label="영상 재생"
              className="w-10 h-10 bg-white/20 backdrop-blur-sm rounded-full flex items-center justify-center border border-white/30">
              <span className="material-symbols-outlined text-white text-2xl" style={{ fontVariationSettings: "'FILL' 1" }}>
                play_arrow
              </span>
            </button>
          </div>
        </div>
        {/* 우측 텍스트 */}
        <div className="flex-1 min-w-0 flex flex-col justify-between">
          <h2 className="text-sm font-bold text-gray-4 dark:text-white leading-snug line-clamp-3">{item.title}</h2>
          <div className="flex items-center gap-3 mt-2 text-gray-2">
            <span className="text-[10px] truncate">{item.channelName}</span>
            <div className="ml-auto flex items-center gap-2.5 shrink-0">
              <span className="flex items-center gap-0.5">
                <span className="material-symbols-outlined text-[14px]">thumb_up</span>
                <span className="text-[10px] font-medium">{formatCount(item.likes)}</span>
              </span>
              <span className="flex items-center gap-0.5">
                <span className="material-symbols-outlined text-[14px]">chat_bubble</span>
                <span className="text-[10px] font-medium">{formatCount(item.comments)}</span>
              </span>
            </div>
          </div>
        </div>
      </div>
    </article>
  );
}
```

- [ ] **Step 4: 테스트 실행 (PASS 확인)**

```bash
cd /home/ubuntu/project/Lawdigest/services/web
npx vitest run app/election/components/feed/YoutubeCard.test.tsx
```

- [ ] **Step 5: 커밋**

```bash
git add services/web/app/election/components/feed/YoutubeCard.tsx \
        services/web/app/election/components/feed/YoutubeCard.test.tsx
git commit -m "feat: YoutubeCard 리디자인 — 수평 썸네일 레이아웃, aria-label 추가"
```

---

## Task 7: BillCard 리디자인 + BillMiniCard 통합

**Files:**
- Create: `services/web/app/election/components/feed/BillCard.tsx`
- Create: `services/web/app/election/components/feed/BillCard.test.tsx`
- Delete: `services/web/app/election/components/BillMiniCard.tsx`

- [ ] **Step 1: 테스트 작성**

```typescript
// BillCard.test.tsx
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import BillCard from './BillCard';

const mockItem = {
  type: 'bill' as const,
  id: 'bill-1',
  briefSummary: '청년 주거 안정을 위한 공공임대주택 확대 법안',
  billName: '공공주택 특별법 일부개정법률안',
  billStage: '위원회 심사',
  proposeDate: '2026-03-15',
  partyName: '더불어민주당',
};

describe('BillCard', () => {
  it('법안 요약을 렌더링한다', () => {
    render(<BillCard item={mockItem} />);
    expect(screen.getByText('청년 주거 안정을 위한 공공임대주택 확대 법안')).toBeInTheDocument();
  });

  it('법안명을 렌더링한다', () => {
    render(<BillCard item={mockItem} />);
    expect(screen.getByText('공공주택 특별법 일부개정법률안')).toBeInTheDocument();
  });

  it('진행 단계를 렌더링한다', () => {
    render(<BillCard item={mockItem} />);
    expect(screen.getByText('위원회 심사')).toBeInTheDocument();
  });

  it('타입 칩을 렌더링한다', () => {
    render(<BillCard item={mockItem} />);
    expect(screen.getByText('법안')).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: 테스트 실행 (FAIL 확인)**

```bash
cd /home/ubuntu/project/Lawdigest/services/web
npx vitest run app/election/components/feed/BillCard.test.tsx
```

- [ ] **Step 3: BillCard 구현**

```typescript
// BillCard.tsx
'use client';

import { BillMiniCardProps } from '../../data/mockFeedData';
import FeedTypeChip from './FeedTypeChip';
import { formatDate } from './utils';

const STAGE_CONFIG: Record<string, { className: string }> = {
  '접수':       { className: 'bg-gray-0.5 dark:bg-dark-l text-gray-2' },
  '위원회 심사': { className: 'bg-blue-50 text-blue-600' },
  '본회의 심의': { className: 'bg-amber-50 text-amber-600' },
  '통과':       { className: 'bg-green-100 text-green-700' },
};

export default function BillCard({ item }: { item: BillMiniCardProps }) {
  const stageClass = STAGE_CONFIG[item.billStage]?.className ?? 'bg-gray-0.5 text-gray-2';
  return (
    <article className="bg-white dark:bg-dark-b p-4 rounded-xl border border-gray-1 dark:border-dark-l shadow-sm">
      {/* 헤더 */}
      <div className="flex items-center gap-2 mb-3">
        <FeedTypeChip type="bill" />
        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${stageClass}`}>{item.billStage}</span>
        <span className="ml-auto text-[10px] text-gray-2 shrink-0">{formatDate(item.proposeDate)}</span>
      </div>
      {/* 본문 */}
      <p className="text-sm font-semibold text-gray-4 dark:text-white leading-snug line-clamp-2 mb-2">
        {item.briefSummary}
      </p>
      {/* 푸터 */}
      <div className="flex items-center justify-between pt-3 border-t border-gray-0.5 dark:border-dark-l/30">
        <span className="text-[11px] text-gray-2 truncate">{item.billName}</span>
        <button
          type="button"
          className="shrink-0 ml-3 text-[11px] font-bold text-primary-2 hover:underline">
          자세히
        </button>
      </div>
    </article>
  );
}
```

- [ ] **Step 4: BillMiniCard.tsx 사용처 확인 후 BillCard로 교체**

```bash
cd /home/ubuntu/project/Lawdigest/services/web
grep -r "BillMiniCard" app/ --include="*.tsx" --include="*.ts" -l
```

BillMiniCard를 import하는 파일에서 BillCard로 교체.

- [ ] **Step 5: components/index.ts에서 BillMiniCard export 제거**

`services/web/app/election/components/index.ts` 25번째 줄 삭제:
```typescript
// 제거할 줄:
export { default as BillMiniCard } from './BillMiniCard';
```

- [ ] **Step 6: BillMiniCard.tsx 삭제**

```bash
rm services/web/app/election/components/BillMiniCard.tsx
rm services/web/app/election/components/BillMiniCard.test.tsx
```

- [ ] **Step 7: 테스트 실행 (PASS 확인)**

```bash
cd /home/ubuntu/project/Lawdigest/services/web
npx vitest run app/election/components/feed/BillCard.test.tsx
```

- [ ] **Step 8: 커밋**

```bash
git add services/web/app/election/components/feed/BillCard.tsx \
        services/web/app/election/components/feed/BillCard.test.tsx \
        services/web/app/election/components/index.ts
git rm services/web/app/election/components/BillMiniCard.tsx \
       services/web/app/election/components/BillMiniCard.test.tsx
git commit -m "feat: BillCard 리디자인 — 흰 배경, 타입 칩, BillMiniCard 통합 및 index.ts 정리"
```

---

## Task 8: ImageCard 타입 칩 통일

**Files:**
- Create: `services/web/app/election/components/feed/ImageCard.tsx`
- Create: `services/web/app/election/components/feed/ImageCard.test.tsx`

- [ ] **Step 1: 테스트 작성**

```typescript
// ImageCard.test.tsx
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import ImageCard from './ImageCard';

const mockItem = {
  type: 'image' as const,
  id: 'img-1',
  groupName: '국민의힘 서울시당',
  partyName: '국민의힘',
  content: '주말 서울 광장 그린업 프로젝트 성공적으로 마쳤습니다!',
  images: [
    { src: 'https://example.com/img1.jpg', alt: '나무 심기 행사' },
    { src: 'https://example.com/img2.jpg', alt: '자원봉사자들' },
  ],
  publishedAt: '2026-04-02T14:00:00Z',
};

describe('ImageCard', () => {
  it('그룹명을 렌더링한다', () => {
    render(<ImageCard item={mockItem} />);
    expect(screen.getByText('국민의힘 서울시당')).toBeInTheDocument();
  });

  it('본문 내용을 렌더링한다', () => {
    render(<ImageCard item={mockItem} />);
    expect(screen.getByText('주말 서울 광장 그린업 프로젝트 성공적으로 마쳤습니다!')).toBeInTheDocument();
  });

  it('타입 칩을 렌더링한다', () => {
    render(<ImageCard item={mockItem} />);
    expect(screen.getByText('이미지')).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: 테스트 실행 (FAIL 확인)**

```bash
cd /home/ubuntu/project/Lawdigest/services/web
npx vitest run app/election/components/feed/ImageCard.test.tsx
```

- [ ] **Step 3: ImageCard 구현** (기존 구조 유지, utils import, 타입 칩 추가)

```typescript
// ImageCard.tsx
'use client';

import Image from 'next/image';
import { ImageFeedItem } from '../../data/mockFeedData';
import FeedTypeChip from './FeedTypeChip';
import { timeAgo } from './utils';

export default function ImageCard({ item }: { item: ImageFeedItem }) {
  return (
    <article className="bg-white dark:bg-dark-b rounded-xl border border-gray-1 dark:border-dark-l shadow-sm overflow-hidden">
      <div className="p-4">
        <div className="flex items-center gap-2 mb-3">
          <FeedTypeChip type="image" />
          <span className="text-xs font-bold text-gray-4 dark:text-white truncate flex-1">{item.groupName}</span>
          <span className="text-[10px] text-gray-2 shrink-0">{timeAgo(item.publishedAt)}</span>
        </div>
        <p className="text-sm text-gray-4 dark:text-white leading-relaxed line-clamp-3">{item.content}</p>
      </div>
      {item.images.length > 0 && (
        <div className={`grid gap-0.5 ${item.images.length >= 2 ? 'grid-cols-2' : 'grid-cols-1'}`}>
          {item.images.slice(0, 4).map((img) => (
            <div key={img.src} className="relative aspect-square w-full">
              <Image src={img.src} alt={img.alt} fill unoptimized className="object-cover" />
            </div>
          ))}
        </div>
      )}
    </article>
  );
}
```

- [ ] **Step 4: 테스트 실행 (PASS 확인)**

```bash
cd /home/ubuntu/project/Lawdigest/services/web
npx vitest run app/election/components/feed/ImageCard.test.tsx
```

- [ ] **Step 5: 커밋**

```bash
git add services/web/app/election/components/feed/ImageCard.tsx \
        services/web/app/election/components/feed/ImageCard.test.tsx
git commit -m "feat: ImageCard 타입 칩 추가 및 구조 통일"
```

---

## Task 9: feed/index.ts + ElectionFeedCardList 교체

**Files:**
- Create: `services/web/app/election/components/feed/index.ts`
- Modify: `services/web/app/election/components/ElectionFeedCardList.tsx`

- [ ] **Step 1: feed/index.ts 작성**

```typescript
// feed/index.ts
export { default as FeedTypeChip } from './FeedTypeChip';
export { default as ActiveFilterBadge } from './ActiveFilterBadge';
export { default as SnsCard } from './SnsCard';
export { default as YoutubeCard } from './YoutubeCard';
export { default as PollCard } from './PollCard';
export { default as BillCard } from './BillCard';
export { default as ImageCard } from './ImageCard';
```

- [ ] **Step 2: ElectionFeedCardList.tsx 교체**

```typescript
// ElectionFeedCardList.tsx
'use client';

import { FeedItem, SnsFeedItem, PollFeedItem, BillMiniCardProps, YoutubeFeedItem, ImageFeedItem } from '../data/mockFeedData';
import { SnsCard, YoutubeCard, PollCard, BillCard, ImageCard } from './feed';

interface ElectionFeedCardListProps {
  items: FeedItem[];
  emptyMessage?: string;
}

export default function ElectionFeedCardList({ items, emptyMessage }: ElectionFeedCardListProps) {
  if (items.length === 0) {
    return (
      <p className="text-center py-12 text-sm text-gray-2">
        {emptyMessage ?? '아직 등록된 선거 피드가 없습니다.'}
      </p>
    );
  }
  return (
    <div className="space-y-3 px-4 pb-6">
      {items.map((item) => {
        if (item.type === 'youtube') return <YoutubeCard key={item.id} item={item as YoutubeFeedItem} />;
        if (item.type === 'sns')     return <SnsCard     key={item.id} item={item as SnsFeedItem} />;
        if (item.type === 'bill')    return <BillCard    key={item.id} item={item as BillMiniCardProps} />;
        if (item.type === 'poll')    return <PollCard    key={item.id} item={item as PollFeedItem} />;
        if (item.type === 'image')   return <ImageCard   key={item.id} item={item as ImageFeedItem} />;
        return null;
      })}
    </div>
  );
}
```

- [ ] **Step 3: 기존 테스트 실행**

```bash
cd /home/ubuntu/project/Lawdigest/services/web
npx vitest run app/election/components/ElectionFeedView.test.tsx
```

- [ ] **Step 4: 커밋**

```bash
git add services/web/app/election/components/feed/index.ts \
        services/web/app/election/components/ElectionFeedCardList.tsx
git commit -m "refactor: ElectionFeedCardList — feed/ 카드 컴포넌트로 교체"
```

---

## Task 10: ElectionFeedView에 ActiveFilterBadge 추가

**Files:**
- Modify: `services/web/app/election/components/ElectionFeedView.tsx`
- Create: `services/web/app/election/components/ElectionFeedView.test.tsx`

- [ ] **Step 1: 통합 테스트 작성 (onClear → subView 리셋 검증)**

```typescript
// ElectionFeedView.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import ElectionFeedView from './ElectionFeedView';

describe('ElectionFeedView — ActiveFilterBadge', () => {
  it('정당별 탭에서 정당 선택 시 필터 배지가 표시된다', async () => {
    render(<ElectionFeedView confirmedRegion={null} />);
    // 정당별 탭 클릭
    fireEvent.click(screen.getByRole('button', { name: '정당별' }));
    // 정당 선택 — PartyRingSelector의 첫 번째 버튼 클릭
    const partyButtons = screen.getAllByRole('button');
    const demButton = partyButtons.find((b) => b.textContent?.includes('더불어민주당'));
    if (demButton) fireEvent.click(demButton);
    expect(screen.getByText(/더불어민주당 필터 적용 중/)).toBeInTheDocument();
  });

  it('필터 배지의 해제 버튼을 클릭하면 전체 탭으로 돌아간다', async () => {
    render(<ElectionFeedView confirmedRegion={null} />);
    fireEvent.click(screen.getByRole('button', { name: '정당별' }));
    const partyButtons = screen.getAllByRole('button');
    const demButton = partyButtons.find((b) => b.textContent?.includes('더불어민주당'));
    if (demButton) fireEvent.click(demButton);
    fireEvent.click(screen.getByRole('button', { name: /해제/ }));
    // 배지 사라짐 확인
    expect(screen.queryByText(/필터 적용 중/)).not.toBeInTheDocument();
  });
});
```

- [ ] **Step 2: 테스트 실행 (FAIL 확인)**

```bash
cd /home/ubuntu/project/Lawdigest/services/web
npx vitest run app/election/components/ElectionFeedView.test.tsx
```

- [ ] **Step 3: ElectionFeedView에 ActiveFilterBadge 연결**

`ElectionFeedView.tsx`에서:
1. `ActiveFilterBadge` import 추가
2. `filterItems()`에 빈 상태 메시지 반환 로직 추가
3. 필터 적용 시 ActiveFilterBadge 표시

```typescript
// ElectionFeedView.tsx 수정 부분

import { ActiveFilterBadge } from './feed';

// filterItems() 아래에 activeFilterLabel 함수 추가:
function activeFilterLabel(): string | null {
  if (subView === 'party' && selectedParty) return selectedParty;
  if (subView === 'region' && selectedRegion) return selectedRegion.regionName;
  return null;
}

function emptyMessage(): string {
  if (subView === 'party' && selectedParty) return `${selectedParty}의 피드가 아직 없습니다.`;
  if (subView === 'region' && selectedRegion) return `${selectedRegion.regionName}의 피드가 아직 없습니다.`;
  return '아직 등록된 선거 피드가 없습니다.';
}

// JSX에서 피드 목록 위에 ActiveFilterBadge 추가:
{(() => {
  const activeLabel = activeFilterLabel();
  return activeLabel ? (
    <ActiveFilterBadge
      label={activeLabel}
      onClear={() => { setSubView('all'); setSelectedParty(null); setSelectedRegion(null); }}
    />
  ) : null;
})()}
<div className="mt-3">
  <ElectionFeedCardList items={filterItems()} emptyMessage={emptyMessage()} />
</div>
```

- [ ] **Step 5: 테스트 실행 (PASS 확인)**

```bash
cd /home/ubuntu/project/Lawdigest/services/web
npx vitest run app/election/components/ElectionFeedView.test.tsx
```

- [ ] **Step 6: 전체 테스트 실행**

```bash
cd /home/ubuntu/project/Lawdigest/services/web
npx vitest run app/election/components/
```

- [ ] **Step 7: 빌드 확인**

```bash
cd /home/ubuntu/project/Lawdigest/services/web
npx tsc --noEmit
```

- [ ] **Step 8: 커밋**

```bash
git add services/web/app/election/components/ElectionFeedView.tsx \
        services/web/app/election/components/ElectionFeedView.test.tsx
git commit -m "feat: ElectionFeedView에 ActiveFilterBadge 연결 및 빈 상태 메시지 컨텍스트화"
```

---

## Task 11: 전체 테스트 및 린트

- [ ] **Step 1: 전체 테스트 실행**

```bash
cd /home/ubuntu/project/Lawdigest/services/web
npx vitest run
```

- [ ] **Step 2: 린트**

```bash
cd /home/ubuntu/project/Lawdigest/services/web
npx eslint app/election/ --ext .tsx,.ts
```

- [ ] **Step 3: 타입 체크**

```bash
cd /home/ubuntu/project/Lawdigest/services/web
npx tsc --noEmit
```

- [ ] **Step 4: 이슈 수정 후 최종 커밋**

```bash
git add -p  # 수정 사항 선택적 스테이징
git commit -m "chore: 피드 탭 리디자인 린트·타입 오류 수정"
```

---

## 완료 기준

- [ ] 5종 카드 모두 `bg-white` 기반 통일 배경
- [ ] 모든 카드 좌상단에 컨텐츠 타입 칩 표시
- [ ] PollCard 바 차트에 정당 컬러 적용 (단색 `bg-primary-2` 제거)
- [ ] SnsCard 아바타 32px 컴팩트 레이아웃
- [ ] YoutubeCard 수평 썸네일 레이아웃 + `aria-label="영상 재생"`
- [ ] BillCard 장식 gavel 아이콘 제거, BillMiniCard.tsx 삭제
- [ ] 필터 적용 시 ActiveFilterBadge 표시 + 해제 버튼
- [ ] 빈 상태 메시지가 필터 컨텍스트에 따라 다르게 표시
- [ ] 전체 테스트 통과
- [ ] TypeScript 오류 없음
