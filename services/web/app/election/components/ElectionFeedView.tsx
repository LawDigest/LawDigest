'use client';

import { useState } from 'react';
import { useGetElectionPollOverview } from '../apis/queries';
import { ConfirmedRegion } from './ElectionMapShell';
import {
  MOCK_FEED_ITEMS,
  FeedItem,
  SnsFeedItem,
  PollFeedItem,
  BillMiniCardProps,
  YoutubeFeedItem,
} from '../data/mockFeedData';
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

interface ElectionFeedViewProps {
  confirmedRegion: ConfirmedRegion | null;
  selectedElectionId: string;
}

function getPartyColor(partyName: string) {
  if (partyName.includes('더불어민주')) return '#152484';
  if (partyName.includes('국민의힘')) return '#C9151E';
  if (partyName === 'undecided') return '#999999';
  return '#5b6475';
}

export default function ElectionFeedView({ confirmedRegion, selectedElectionId }: ElectionFeedViewProps) {
  const [subView, setSubView] = useState<FeedSubView>('all');
  const [selectedParty, setSelectedParty] = useState<string | null>(null);
  const [selectedRegion, setSelectedRegion] = useState<SelectedRegion | null>(
    confirmedRegion ? { regionCode: confirmedRegion.regionCode, regionName: confirmedRegion.regionName } : null,
  );

  const regionCode = selectedRegion?.regionCode ?? confirmedRegion?.regionCode ?? '';
  const regionName = selectedRegion?.regionName ?? confirmedRegion?.regionName ?? '';
  const pollOverviewQuery = useGetElectionPollOverview(selectedElectionId, regionCode, !!regionCode);

  const realPollItems: PollFeedItem[] =
    pollOverviewQuery.data?.data.latest_surveys.map((survey) => ({
      type: 'poll',
      id: `poll-${survey.registration_number}`,
      pollster: survey.pollster,
      sponsor: survey.sponsor,
      questionTitle: survey.question_title,
      sampleSize: survey.sample_size,
      marginOfError: survey.margin_of_error,
      publishedAt: `${survey.survey_end_date}T00:00:00Z`,
      results: survey.snapshot.map((snapshot) => ({
        partyName: snapshot.party_name,
        pct: snapshot.percentage,
        delta: 0,
        color: getPartyColor(snapshot.party_name),
      })),
      region: regionName,
    })) ?? [];

  const feedItems = [...MOCK_FEED_ITEMS.filter((item) => item.type !== 'poll'), ...realPollItems];

  const parties =
    pollOverviewQuery.data?.data.latest_surveys?.[0]?.snapshot
      ?.filter((snapshot) => snapshot.party_name !== 'undecided')
      .map((snapshot) => ({ name: snapshot.party_name, color: getPartyColor(snapshot.party_name) })) ?? [];

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
      return feedItems.filter((item) => {
        if (item.type === 'sns') return (item as SnsFeedItem).partyName === selectedParty;
        if (item.type === 'youtube') return (item as YoutubeFeedItem).partyName === selectedParty;
        if (item.type === 'poll') return (item as PollFeedItem).results.some((r) => r.partyName === selectedParty);
        if (item.type === 'bill') return (item as BillMiniCardProps).partyName === selectedParty;
        if (item.type === 'image') return item.partyName === selectedParty;
        return true;
      });
    }
    if (subView === 'region' && selectedRegion?.regionName) {
      return feedItems.filter((item) =>
        'region' in item ? (item as SnsFeedItem | PollFeedItem).region === selectedRegion.regionName : true,
      );
    }
    return feedItems;
  }

  return (
    <div className="flex flex-col">
      {/* 서브 뷰 탭 */}
      <SubTabBar tabs={SUB_TABS} active={subView} onChange={setSubView} />

      {/* 서브 필터 영역 */}
      {subView === 'party' && (
        <PartyRingSelector parties={parties} selected={selectedParty} onSelect={setSelectedParty} />
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
