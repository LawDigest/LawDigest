'use client';

import { useState } from 'react';
import { Layout } from '@/components';
import ElectionDdayHeader from './ElectionDdayHeader';
import ElectionInnerTabBar, { ElectionInnerTab } from './ElectionInnerTabBar';
import ElectionMapTabView from './ElectionMapTabView';

// 2026 전국동시지방선거
const LOCAL_ELECTION_DATE = new Date('2026-06-03');
const LOCAL_ELECTION_NAME = '제8회 전국동시지방선거';

export default function ElectionMapShell() {
  const [activeTab, setActiveTab] = useState<ElectionInnerTab>('map');

  return (
    <Layout nav logo>
      <div className="flex flex-col w-full md:max-w-[768px] mx-auto">
        <ElectionDdayHeader electionName={LOCAL_ELECTION_NAME} electionDate={LOCAL_ELECTION_DATE} />

        <ElectionInnerTabBar activeTab={activeTab} onChange={setActiveTab} />

        {activeTab === 'map' && <ElectionMapTabView />}

        {activeTab !== 'map' && (
          <div className="flex flex-col items-center justify-center min-h-[320px] gap-3 text-gray-2">
            <p className="text-sm">
              {activeTab === 'feed' && '피드'}
              {activeTab === 'poll' && '여론조사'}
              {activeTab === 'district' && '내 지역구'} 탭은 준비 중입니다.
            </p>
          </div>
        )}
      </div>
    </Layout>
  );
}
