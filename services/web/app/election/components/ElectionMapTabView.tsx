'use client';

import { useState } from 'react';
import MapViewToggle, { MapViewMode } from './MapViewToggle';
import SeatSummaryCard from './SeatSummaryCard';
import RegionResultGrid from './RegionResultGrid';

// 프로토타입용 목업 데이터
const MOCK_PARTIES = [
  { name: '더불어민주당', seats: 160, colorClass: 'bg-party-minjoo' },
  { name: '국민의힘', seats: 114, colorClass: 'bg-party-ppp' },
  { name: '기타', seats: 26, colorClass: 'bg-party-independent' },
];

const MOCK_REGIONS = [
  {
    regionName: '서울',
    leadingParty: '더불어민주당',
    leadingPartyShort: '민주',
    percentage: 51.8,
    partyColorClass: 'bg-party-minjoo',
  },
  {
    regionName: '경기',
    leadingParty: '더불어민주당',
    leadingPartyShort: '민주',
    percentage: 54.2,
    partyColorClass: 'bg-party-minjoo',
  },
  {
    regionName: '인천',
    leadingParty: '더불어민주당',
    leadingPartyShort: '민주',
    percentage: 52.1,
    partyColorClass: 'bg-party-minjoo',
  },
  {
    regionName: '부산',
    leadingParty: '국민의힘',
    leadingPartyShort: '국힘',
    percentage: 58.3,
    partyColorClass: 'bg-party-ppp',
  },
  {
    regionName: '경남',
    leadingParty: '국민의힘',
    leadingPartyShort: '국힘',
    percentage: 60.4,
    partyColorClass: 'bg-party-ppp',
  },
  {
    regionName: '대구',
    leadingParty: '국민의힘',
    leadingPartyShort: '국힘',
    percentage: 66.1,
    partyColorClass: 'bg-party-ppp',
  },
  {
    regionName: '경북',
    leadingParty: '국민의힘',
    leadingPartyShort: '국힘',
    percentage: 72.1,
    partyColorClass: 'bg-party-ppp',
  },
  {
    regionName: '강원',
    leadingParty: '국민의힘',
    leadingPartyShort: '국힘',
    percentage: 64.2,
    partyColorClass: 'bg-party-ppp',
  },
  {
    regionName: '대전',
    leadingParty: '더불어민주당',
    leadingPartyShort: '민주',
    percentage: 49.7,
    partyColorClass: 'bg-party-minjoo',
  },
  {
    regionName: '충남',
    leadingParty: '더불어민주당',
    leadingPartyShort: '민주',
    percentage: 48.3,
    partyColorClass: 'bg-party-minjoo',
  },
  {
    regionName: '전남',
    leadingParty: '더불어민주당',
    leadingPartyShort: '민주',
    percentage: 67.5,
    partyColorClass: 'bg-party-minjoo',
  },
  {
    regionName: '전북',
    leadingParty: '더불어민주당',
    leadingPartyShort: '민주',
    percentage: 65.9,
    partyColorClass: 'bg-party-minjoo',
  },
];

export default function ElectionMapTabView() {
  const [viewMode, setViewMode] = useState<MapViewMode>('geographic');

  return (
    <div className="flex flex-col gap-5 pb-32">
      <SeatSummaryCard totalSeats={300} countRate={98.2} parties={MOCK_PARTIES} />

      {/* 지도 영역 */}
      <section className="mx-5 flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <p className="text-xs font-semibold tracking-widest text-gray-2 uppercase">선거 지도</p>
          <MapViewToggle value={viewMode} onChange={setViewMode} />
        </div>

        <div className="relative flex min-h-[240px] items-center justify-center rounded-2xl bg-gray-0.5 dark:bg-dark-pb overflow-hidden">
          {/* 실제 지도 / 카토그램 렌더링 영역 (추후 D3 연동 예정) */}
          <div className="flex flex-col items-center gap-2 text-gray-2 text-sm">
            <svg width="40" height="40" viewBox="0 0 40 40" fill="none" className="opacity-30">
              <rect x="4" y="4" width="14" height="14" rx="3" fill="currentColor" />
              <rect x="22" y="4" width="14" height="14" rx="3" fill="currentColor" />
              <rect x="4" y="22" width="14" height="14" rx="3" fill="currentColor" />
              <rect x="22" y="22" width="14" height="14" rx="3" fill="currentColor" />
            </svg>
            <span>{viewMode === 'geographic' ? '실제 지도' : '카토그램'} 렌더링 영역</span>
            <span className="text-xs text-gray-2 opacity-60">D3 시각화 연동 예정</span>
          </div>
        </div>
      </section>

      <RegionResultGrid
        regions={MOCK_REGIONS}
        onRegionClick={(name) => {
          // 추후 지역 드릴다운 연동
          // eslint-disable-next-line no-console
          console.debug('region clicked:', name);
        }}
      />
    </div>
  );
}
