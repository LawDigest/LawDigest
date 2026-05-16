'use client';

import { getPartyColor, UNKNOWN_PARTY_COLOR } from '@/constants/party';
import SeatSummaryCard from './SeatSummaryCard';
import RegionResultGrid from './RegionResultGrid';
import MapRegionCarousel from './MapRegionCarousel';

// 프로토타입용 목업 데이터 (지방선거 광역단체장 기준, 총 17곳)
const MOCK_GOVERNOR_PARTIES = [
  { name: '더불어민주당', seats: 9, color: getPartyColor('더불어민주당') },
  { name: '국민의힘', seats: 7, color: getPartyColor('국민의힘') },
  { name: '기타', seats: 1, color: UNKNOWN_PARTY_COLOR },
];

const MOCK_POLL_SEGMENTS = [
  { label: '민주 우세', count: 9, color: getPartyColor('더불어민주당') },
  { label: '경합', count: 6, color: UNKNOWN_PARTY_COLOR },
  { label: '국힘 우세', count: 2, color: getPartyColor('국민의힘') },
];

const MOCK_REGIONS = [
  {
    regionName: '서울',
    leadingParty: '더불어민주당',
    leadingPartyShort: '민주',
    percentage: 51.8,
    partyColor: getPartyColor('더불어민주당'),
  },
  {
    regionName: '경기',
    leadingParty: '더불어민주당',
    leadingPartyShort: '민주',
    percentage: 54.2,
    partyColor: getPartyColor('더불어민주당'),
  },
  {
    regionName: '인천',
    leadingParty: '더불어민주당',
    leadingPartyShort: '민주',
    percentage: 52.1,
    partyColor: getPartyColor('더불어민주당'),
  },
  {
    regionName: '부산',
    leadingParty: '국민의힘',
    leadingPartyShort: '국힘',
    percentage: 58.3,
    partyColor: getPartyColor('국민의힘'),
  },
  {
    regionName: '경남',
    leadingParty: '국민의힘',
    leadingPartyShort: '국힘',
    percentage: 60.4,
    partyColor: getPartyColor('국민의힘'),
  },
  {
    regionName: '대구',
    leadingParty: '국민의힘',
    leadingPartyShort: '국힘',
    percentage: 66.1,
    partyColor: getPartyColor('국민의힘'),
  },
  {
    regionName: '경북',
    leadingParty: '국민의힘',
    leadingPartyShort: '국힘',
    percentage: 72.1,
    partyColor: getPartyColor('국민의힘'),
  },
  {
    regionName: '강원',
    leadingParty: '국민의힘',
    leadingPartyShort: '국힘',
    percentage: 64.2,
    partyColor: getPartyColor('국민의힘'),
  },
  {
    regionName: '대전',
    leadingParty: '더불어민주당',
    leadingPartyShort: '민주',
    percentage: 49.7,
    partyColor: getPartyColor('더불어민주당'),
  },
  {
    regionName: '충남',
    leadingParty: '더불어민주당',
    leadingPartyShort: '민주',
    percentage: 48.3,
    partyColor: getPartyColor('더불어민주당'),
  },
  {
    regionName: '전남',
    leadingParty: '더불어민주당',
    leadingPartyShort: '민주',
    percentage: 67.5,
    partyColor: getPartyColor('더불어민주당'),
  },
  {
    regionName: '전북',
    leadingParty: '더불어민주당',
    leadingPartyShort: '민주',
    percentage: 65.9,
    partyColor: getPartyColor('더불어민주당'),
  },
];

export default function ElectionMapTabView() {
  return (
    <div className="flex flex-col gap-5 pb-32 pt-4">
      {/* 지도 영역 */}
      <section className="mx-5 flex flex-col gap-3">
        <p className="text-xs font-semibold tracking-widest text-gray-2 uppercase">선거 지도</p>
        <div className="rounded-xl bg-white dark:bg-dark-pb border border-gray-1 dark:border-dark-l shadow-none overflow-hidden px-3 pt-3 pb-4">
          <MapRegionCarousel />
        </div>
      </section>

      <SeatSummaryCard totalRegions={17} governorParties={MOCK_GOVERNOR_PARTIES} pollSegments={MOCK_POLL_SEGMENTS} />

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
