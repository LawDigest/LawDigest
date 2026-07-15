'use client';

import { Suspense, useState } from 'react';
import { Spinner } from '@heroui/spinner';
import AssemblySegment, { AssemblySegmentValue } from './AssemblySegment';
import SeatDistribution from './SeatDistribution';
import MemberRanking from './MemberRanking';
import MemberList from './MemberList';
import PartyList from './PartyList';

/** 국회 패널 — 의원(의석 분포·발의 랭킹·전체 리스트) / 정당(원내 정당 목록). */
export default function AssemblyPanel() {
  const [segment, setSegment] = useState<AssemblySegmentValue>('member');

  return (
    <div className="flex flex-col gap-6">
      <AssemblySegment active={segment} onChange={setSegment} />

      {segment === 'member' ? (
        <>
          <SeatDistribution />
          <MemberRanking />
          <section className="flex flex-col gap-3">
            <h2 className="text-[15px] font-bold text-primary-3 dark:text-gray-0.5">의원 전체</h2>
            <Suspense
              fallback={
                <div className="flex justify-center py-8">
                  <Spinner color="default" />
                </div>
              }>
              <MemberList />
            </Suspense>
          </section>
        </>
      ) : (
        <PartyList />
      )}
    </div>
  );
}
