'use client';

import React, { forwardRef } from 'react';
import { MOCK_POLL_DATA } from '../data/mockPollData';
import type { ProvinceElectionInfo } from './KoreaMap';

interface ProvinceInfoCardProps {
  provinceName: string;
  info: ProvinceElectionInfo;
  side: 'left' | 'right';
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
        'flex flex-col gap-[2px] w-[84px]',
        side === 'left' ? 'border-r-[2px] pr-1' : 'border-l-[2px] pl-1',
      ].join(' ')}
      style={{
        borderRightColor: side === 'left' ? leadingColor : undefined,
        borderLeftColor: side === 'right' ? leadingColor : undefined,
      }}>
      {/* 직책명 */}
      <p className="text-[7px] font-bold text-black leading-tight truncate">{info.title}</p>

      {/* 후보명 행 */}
      <div className="flex justify-between gap-1">
        <span className="text-[7px] text-gray-700 truncate">{info.c1.name}</span>
        <span className="text-[7px] text-gray-700 truncate">{info.c2.name}</span>
      </div>

      {/* 수평 바 차트 */}
      <div className="h-[5px] rounded-full overflow-hidden flex">
        <div
          className="rounded-full origin-left animate-bar-grow"
          style={{ width: `${c1Pct}%`, backgroundColor: info.c1.color }}
        />
        {otherPct > 0 && <div style={{ width: `${otherPct}%`, backgroundColor: '#D1D5DB' }} />}
        <div
          className="rounded-full origin-right animate-bar-grow"
          style={{ width: `${c2Pct}%`, backgroundColor: info.c2.color }}
        />
      </div>

      {/* 지지율 행 */}
      <div className="flex justify-between gap-1">
        <span className="text-[7px] font-bold" style={{ color: info.c1.color }}>
          {c1Pct.toFixed(0)}%
        </span>
        <span className="text-[7px] font-bold" style={{ color: info.c2.color }}>
          {c2Pct.toFixed(0)}%
        </span>
      </div>
    </div>
  );
});
ProvinceInfoCard.displayName = 'ProvinceInfoCard';

export default ProvinceInfoCard;
