'use client';

import { MOCK_POLL_DATA } from '../data/mockPollData';

interface PollRegionPanelProps {
  region: string;
}

export default function PollRegionPanel({ region }: PollRegionPanelProps) {
  const pollData = MOCK_POLL_DATA[region];

  return (
    <div className="space-y-3 px-4">
      <h3 className="text-sm font-semibold text-gray-4 dark:text-white">{region} 여론조사</h3>
      {pollData ? (
        <div className="rounded-2xl border border-gray-1 dark:border-dark-l bg-white dark:bg-dark-pb p-4 space-y-3">
          <p className="text-[11px] text-gray-2">{pollData.source}</p>
          {[
            { name: '더불어민주당', pct: pollData.c1Pct, color: '#152484' },
            { name: '국민의힘', pct: pollData.c2Pct, color: '#C9151E' },
            { name: '기타', pct: pollData.otherPct, color: '#999' },
          ].map((item) => (
            <div key={item.name} className="space-y-1">
              <div className="flex justify-between text-xs">
                <span className="text-gray-3 dark:text-gray-1">{item.name}</span>
                <span className="font-semibold text-gray-4 dark:text-white">{item.pct}%</span>
              </div>
              <div className="h-2 w-full rounded-full bg-default-100 dark:bg-dark-b overflow-hidden">
                <div className="h-full rounded-full" style={{ width: `${item.pct}%`, backgroundColor: item.color }} />
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-sm text-gray-2">해당 지역의 여론조사 결과가 없습니다.</p>
      )}
    </div>
  );
}
