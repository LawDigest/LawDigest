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
