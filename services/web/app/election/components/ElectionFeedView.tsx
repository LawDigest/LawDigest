'use client';

import { useState } from 'react';
import { ConfirmedRegion } from './ElectionMapShell';
import {
  MOCK_FEED_ITEMS,
  FeedItem,
  SnsFeedItem,
  PollFeedItem,
  BillMiniCardProps,
  YoutubeFeedItem,
} from '../data/mockFeedData';
import { MOCK_PARTY_POLL_DATA } from '../data/mockPartyPollData';
import PartyRingSelector from './shared/PartyRingSelector';
import DistrictMapPicker, { SelectedRegion } from './shared/DistrictMapPicker';
import ElectionFeedCardList from './ElectionFeedCardList';
import SubTabBar from './shared/SubTabBar';
import { ActiveFilterBadge } from './feed';

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

  function filterItems(): FeedItem[] {
    if (subView === 'party' && selectedParty) {
      return MOCK_FEED_ITEMS.filter((item) => {
        if (item.type === 'sns') return (item as SnsFeedItem).partyName === selectedParty;
        if (item.type === 'youtube') return (item as YoutubeFeedItem).partyName === selectedParty;
        if (item.type === 'poll') return (item as PollFeedItem).results.some((r) => r.partyName === selectedParty);
        if (item.type === 'bill') return (item as BillMiniCardProps).partyName === selectedParty;
        if (item.type === 'image') return item.partyName === selectedParty;
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
      <SubTabBar tabs={SUB_TABS} active={subView} onChange={setSubView} />

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

      {/* 활성 필터 배지 */}
      {(() => {
        const activeLabel = activeFilterLabel();
        return activeLabel ? (
          <ActiveFilterBadge
            label={activeLabel}
            onClear={() => {
              setSubView('all');
              setSelectedParty(null);
              setSelectedRegion(null);
            }}
          />
        ) : null;
      })()}

      {/* 피드 카드 리스트 */}
      <div className="mt-3">
        <ElectionFeedCardList items={filterItems()} emptyMessage={emptyMessage()} />
      </div>
    </div>
  );
}
