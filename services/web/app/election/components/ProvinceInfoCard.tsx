'use client';

import React, { forwardRef } from 'react';
import { MOCK_POLL_DATA } from '../data/mockPollData';
import type { CandidateInfo, ProvinceElectionInfo } from './KoreaMap';

interface ProvinceInfoCardProps {
  provinceName: string;
  info: ProvinceElectionInfo;
  side: 'left' | 'right';
}

function CandidateRow({ candidate, pct }: { candidate: CandidateInfo; pct: number }) {
  return (
    <div className="flex items-center gap-0.5">
      <span
        className="inline-flex items-center justify-center w-3 h-3 rounded-full text-white shrink-0"
        style={{ backgroundColor: candidate.color, fontSize: 5, fontWeight: 700 }}>
        {candidate.party.slice(0, 1)}
      </span>
      <span className="text-[7px] text-gray-700 flex-1 truncate">{candidate.name}</span>
      <span className="text-[7px] font-bold shrink-0" style={{ color: candidate.color }}>
        {pct.toFixed(0)}%
      </span>
    </div>
  );
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
        'flex flex-col gap-0.5 w-[80px]',
        side === 'left' ? 'border-r-[2px] pr-1' : 'border-l-[2px] pl-1',
      ].join(' ')}
      style={{
        borderRightColor: side === 'left' ? leadingColor : undefined,
        borderLeftColor: side === 'right' ? leadingColor : undefined,
      }}>
      {/* 직책명 */}
      <p className="text-[7px] text-gray-500 leading-tight truncate">{info.title}</p>

      {/* 후보 2명 */}
      <CandidateRow candidate={info.c1} pct={c1Pct} />
      <CandidateRow candidate={info.c2} pct={c2Pct} />

      {/* 수평 바 차트 */}
      <div className="h-1 rounded-full overflow-hidden flex">
        <div style={{ width: `${c1Pct}%`, backgroundColor: info.c1.color }} />
        <div style={{ width: `${otherPct}%`, backgroundColor: '#D1D5DB' }} />
        <div style={{ width: `${c2Pct}%`, backgroundColor: info.c2.color }} />
      </div>
    </div>
  );
});
ProvinceInfoCard.displayName = 'ProvinceInfoCard';

export default ProvinceInfoCard;
