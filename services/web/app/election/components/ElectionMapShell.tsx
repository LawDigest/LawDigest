'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { Layout } from '@/components';
import { useGetElectionSelector } from '../apis/queries';
import { compareElectionSelectorItems, getDefaultElectionId } from '../utils/compareRules';
import ElectionHeader from './ElectionHeader';
import ElectionInnerTabBar, { ElectionInnerTab } from './ElectionInnerTabBar';
import ElectionMapTabView from './ElectionMapTabView';
import ElectionFeedView from './ElectionFeedView';
import ElectionPollView from './ElectionPollView';
import ElectionDistrictView from './ElectionDistrictView';
import ElectionSelector from './ElectionSelector';

// 2026 전국동시지방선거
const LOCAL_ELECTION_DDAY_TARGET_DATE = new Date(2026, 5, 3);
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
  const searchParams = useSearchParams();
  const selectorQuery = useGetElectionSelector();

  const initialTab: ElectionInnerTab = (() => {
    const tabParam = searchParams.get('tab');
    return isValidTab(tabParam) ? tabParam : 'map';
  })();

  const [activeTab, setActiveTab] = useState<ElectionInnerTab>(initialTab);
  const [confirmedRegion, setConfirmedRegion] = useState<ConfirmedRegion | null>(DEFAULT_REGION);
  const [selectedElectionId, setSelectedElectionId] = useState('local-2026');

  const sortedElections = useMemo(
    () => [...(selectorQuery.data?.data.elections ?? [])].sort(compareElectionSelectorItems),
    [selectorQuery.data?.data.elections],
  );

  useEffect(() => {
    if (!selectorQuery.data?.data) {
      return;
    }

    setSelectedElectionId((current) => {
      if (selectorQuery.data?.data.elections.some((election) => election.election_id === current)) {
        return current;
      }
      return getDefaultElectionId(selectorQuery.data.data);
    });
  }, [selectorQuery.data?.data]);

  const selectedElection = useMemo(
    () => sortedElections.find((election) => election.election_id === selectedElectionId) ?? null,
    [selectedElectionId, sortedElections],
  );

  const electionName = selectedElection?.election_name ?? LOCAL_ELECTION_NAME;

  const handleTabChange = useCallback((tab: ElectionInnerTab) => {
    setActiveTab(tab);

    if (typeof window === 'undefined') {
      return;
    }
    const url = new URL(window.location.href);
    url.searchParams.set('tab', tab);
    window.history.replaceState(window.history.state, '', url.toString());
  }, []);

  return (
    <Layout nav logo>
      <div className="flex w-full flex-col">
        <ElectionHeader electionName={electionName} electionDate={LOCAL_ELECTION_DDAY_TARGET_DATE} />
        {sortedElections.length > 0 && (
          <div className="px-5 pt-4">
            <ElectionSelector
              elections={sortedElections}
              selectedElectionId={selectedElectionId}
              onChange={setSelectedElectionId}
            />
          </div>
        )}
        <ElectionInnerTabBar activeTab={activeTab} onChange={handleTabChange} />

        {activeTab === 'map' && <ElectionMapTabView />}
        {activeTab === 'feed' && (
          <ElectionFeedView confirmedRegion={confirmedRegion} selectedElectionId={selectedElectionId} />
        )}
        {activeTab === 'poll' && (
          <ElectionPollView confirmedRegion={confirmedRegion} selectedElectionId={selectedElectionId} />
        )}
        {activeTab === 'district' && (
          <ElectionDistrictView
            confirmedRegion={confirmedRegion}
            selectedElectionId={selectedElectionId}
            onRegionChange={setConfirmedRegion}
          />
        )}
      </div>
    </Layout>
  );
}
