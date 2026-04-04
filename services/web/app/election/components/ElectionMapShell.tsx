'use client';

import { useState } from 'react';
import { Layout } from '@/components';
import ElectionDdayHeader from './ElectionDdayHeader';
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
