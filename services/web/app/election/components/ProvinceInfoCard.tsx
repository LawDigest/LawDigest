'use client';

import React, { forwardRef } from 'react';
import { MOCK_POLL_DATA } from '../data/mockPollData';
import type { CandidateInfo, ProvinceElectionInfo } from './KoreaMap';

interface ProvinceInfoCardProps {
  provinceName: string;
  info: ProvinceElectionInfo;
  /** 지시선이 나가는 방향 */
  side: 'left' | 'right';
}

function PartyBadge({ party, color }: { party: string; color: string }) {
  return (
    <span
      className="inline-flex items-center justify-center w-[18px] h-[18px] rounded-full text-white shrink-0"
      style={{ backgroundColor: color, fontSize: 7, fontWeight: 700 }}>
      {party.slice(0, 2)}
    </span>
  );
}

function CandidateRow({ candidate, pct }: { candidate: CandidateInfo; pct: number }) {
  return (
    <div className="flex items-center gap-1">
      <PartyBadge party={candidate.party} color={candidate.color} />
      <span className="text-[8px] text-gray-700 flex-1 truncate">{candidate.name}</span>
      <span className="text-[8px] font-bold shrink-0" style={{ color: candidate.color }}>
        {pct.toFixed(1)}%
      </span>
    </div>
  );
}

/** 시도명에서 행정 구분어를 제거해 짧은 이름 반환 */
function shortenProvinceName(name: string): string {
  return name
    .replace('특별자치도', '')
    .replace('특별자치시', '')
    .replace('특별시', '')
    .replace('광역시', '')
    .replace(/도$/, '');
}

const ProvinceInfoCard = forwardRef<HTMLDivElement, ProvinceInfoCardProps>(({ provinceName, info, side }, ref) => {
  const poll = MOCK_POLL_DATA[provinceName];
  const c1Leading = !poll || poll.c1Pct >= poll.c2Pct;
  const leadingColor = c1Leading ? info.c1.color : info.c2.color;

  const c1Pct = poll?.c1Pct ?? 50;
  const c2Pct = poll?.c2Pct ?? 50;
  const otherPct = poll?.otherPct ?? 0;

  return (
    <div
      ref={ref}
      className={[
        'bg-white rounded-lg shadow-sm border border-gray-100 p-1.5',
        'flex flex-col gap-1 w-[105px]',
        side === 'left' ? 'border-r-2' : 'border-l-2',
      ].join(' ')}
      style={{
        borderRightColor: side === 'left' ? leadingColor : undefined,
        borderLeftColor: side === 'right' ? leadingColor : undefined,
      }}>
      {/* 지역명 + 선거직 */}
      <div>
        <p className="text-[10px] font-bold text-gray-800 leading-tight">{shortenProvinceName(provinceName)}</p>
        <p className="text-[8px] text-gray-400 leading-tight truncate">{info.title}</p>
      </div>

      {/* 후보 2명 */}
      <div className="flex flex-col gap-0.5">
        <CandidateRow candidate={info.c1} pct={c1Pct} />
        <CandidateRow candidate={info.c2} pct={c2Pct} />
      </div>

      {/* 수평 바 차트 */}
      <div className="h-1.5 rounded-full overflow-hidden flex">
        <div style={{ width: `${c1Pct}%`, backgroundColor: info.c1.color }} />
        <div style={{ width: `${otherPct}%`, backgroundColor: '#D1D5DB' }} />
        <div style={{ width: `${c2Pct}%`, backgroundColor: info.c2.color }} />
      </div>
    </div>
  );
});
ProvinceInfoCard.displayName = 'ProvinceInfoCard';

export default ProvinceInfoCard;
