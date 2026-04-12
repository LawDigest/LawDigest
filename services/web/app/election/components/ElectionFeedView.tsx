'use client';

import { useEffect, useRef, useState } from 'react';
import { ElectionFeedItem, BillFeedPayload, PollFeedPayload } from '@/types';
import { useGetElectionFeed } from '../apis/queries';
import { ConfirmedRegion } from './ElectionMapShell';
import { BillMiniCardProps, PollFeedItem } from '../data/mockFeedData';
import PartyRingSelector from './shared/PartyRingSelector';
import DistrictMapPicker, { SelectedRegion } from './shared/DistrictMapPicker';
import SubTabBar from './shared/SubTabBar';
import { ActiveFilterBadge, BillCard, PledgeCard, PollCard, ScheduleCard } from './feed';

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

function renderFeedItem(item: ElectionFeedItem) {
  if (item.type === 'pledge') {
    return <PledgeCard key={item.id} item={item} />;
  }
  if (item.type === 'schedule') {
    return <ScheduleCard key={item.id} item={item} />;
  }
  if (item.type === 'bill') {
    const p = item.payload as BillFeedPayload;
    const adapted: BillMiniCardProps = {
      type: 'bill',
      id: item.id,
      briefSummary: p.summary ?? p.bill_name ?? '',
      billName: p.bill_name ?? '',
      billStage: p.stage ?? '',
      proposeDate: p.propose_date ?? item.published_at,
      partyName: p.proposers ?? '',
    };
    return <BillCard key={item.id} item={adapted} />;
  }
  if (item.type === 'poll') {
    const p = item.payload as PollFeedPayload;
    const adapted: PollFeedItem = {
      type: 'poll',
      id: item.id,
      pollster: p.pollster ?? '',
      sponsor: p.sponsor ?? undefined,
      sampleSize: p.sample_size ?? undefined,
      marginOfError: p.margin_of_error ?? undefined,
      publishedAt: item.published_at,
      results: [],
      region: p.region ?? '',
    };
    return <PollCard key={item.id} item={adapted} />;
  }
  return null;
}

export default function ElectionFeedView({ confirmedRegion, selectedElectionId }: ElectionFeedViewProps) {
  const [subView, setSubView] = useState<FeedSubView>('all');
  const [selectedParty, setSelectedParty] = useState<string | null>(null);
  const [selectedRegion, setSelectedRegion] = useState<SelectedRegion | null>(
    confirmedRegion ? { regionCode: confirmedRegion.regionCode, regionName: confirmedRegion.regionName } : null,
  );
  const sentinelRef = useRef<HTMLDivElement>(null);

  const partyFilter = subView === 'party' ? selectedParty : null;
  const regionFilter = subView === 'region' || subView === 'candidate' ? selectedRegion?.regionCode ?? null : null;

  const feedQuery = useGetElectionFeed(selectedElectionId, null, partyFilter, regionFilter);

  const allItems: ElectionFeedItem[] = feedQuery.data?.pages.flatMap((page) => page.data.items) ?? [];

  useEffect(() => {
    const sentinel = sentinelRef.current;
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && feedQuery.hasNextPage && !feedQuery.isFetchingNextPage) {
          feedQuery.fetchNextPage();
        }
      },
      { rootMargin: '200px' },
    );

    if (sentinel) {
      observer.observe(sentinel);
    }

    return () => observer.disconnect();
  }, [feedQuery]);

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

  return (
    <div className="flex flex-col">
      {/* 서브 뷰 탭 */}
      <SubTabBar tabs={SUB_TABS} active={subView} onChange={setSubView} />

      {/* 서브 필터 영역 */}
      {subView === 'party' && <PartyRingSelector parties={[]} selected={selectedParty} onSelect={setSelectedParty} />}
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
      <div className="mt-3 space-y-3 px-4 pb-6">
        {feedQuery.isLoading && <p className="text-center py-12 text-sm text-gray-400">피드를 불러오는 중...</p>}
        {!feedQuery.isLoading && allItems.length === 0 && (
          <p className="text-center py-12 text-sm text-gray-400">{emptyMessage()}</p>
        )}
        {allItems.map(renderFeedItem)}

        {/* 무한 스크롤 sentinel */}
        <div ref={sentinelRef} className="h-1" />

        {feedQuery.isFetchingNextPage && <p className="text-center py-4 text-sm text-gray-400">더 불러오는 중...</p>}
        {!feedQuery.hasNextPage && allItems.length > 0 && (
          <p className="text-center py-4 text-xs text-gray-300">모든 피드를 불러왔습니다.</p>
        )}
      </div>
    </div>
  );
}
