'use client';

import { useCallback, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Layout } from '@/components';
import ElectionHeader from './ElectionHeader';
import ElectionInnerTabBar, { ElectionInnerTab } from './ElectionInnerTabBar';
import ElectionMapTabView from './ElectionMapTabView';
import ElectionFeedView from './ElectionFeedView';
import ElectionPollView from './ElectionPollView';
import ElectionDistrictView from './ElectionDistrictView';

// 2026 전국동시지방선거
const LOCAL_ELECTION_DATE = new Date('2026-06-03');
const LOCAL_ELECTION_NAME = '제9회 전국동시지방선거';

export interface ConfirmedRegion {
  regionCode: string; // e.g. '11'
  regionName: string; // e.g. '서울특별시'
}

const DEFAULT_REGION: ConfirmedRegion = { regionCode: '11', regionName: '서울특별시' };

const VALID_TABS: ElectionInnerTab[] = ['map', 'feed', 'poll', 'district'];

function isValidTab(value: string | null): value is ElectionInnerTab {
  return VALID_TABS.includes(value as ElectionInnerTab);
}

export default function ElectionMapShell() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const tabParam = searchParams.get('tab');
  const activeTab: ElectionInnerTab = isValidTab(tabParam) ? tabParam : 'map';

  const [confirmedRegion, setConfirmedRegion] = useState<ConfirmedRegion | null>(DEFAULT_REGION);

  const handleTabChange = useCallback(
    (tab: ElectionInnerTab) => {
      const params = new URLSearchParams(searchParams.toString());
      params.set('tab', tab);
      router.push(`?${params.toString()}`, { scroll: false });
    },
    [router, searchParams],
  );

  return (
    <Layout nav logo>
      <div className="flex flex-col w-full md:max-w-[768px] mx-auto">
        <ElectionHeader electionName={LOCAL_ELECTION_NAME} electionDate={LOCAL_ELECTION_DATE} />
        <ElectionInnerTabBar activeTab={activeTab} onChange={handleTabChange} />

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
