'use client';

import StatsOverview from './StatsOverview';
import StatsStageFunnel from './StatsStageFunnel';
import StatsPartyBars from './StatsPartyBars';
import StatsCategoryDonut from './StatsCategoryDonut';
import StatsTrend from './StatsTrend';

/** 통계 패널 — 제22대 국회 입법 데이터 대시보드. */
export default function StatsPanel() {
  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-1.5">
        <span className="material-symbols-outlined text-[18px] text-gray-2">calendar_month</span>
        <span className="text-[13px] font-medium text-gray-3 dark:text-gray-1">제22대 국회</span>
      </div>

      <StatsOverview />

      <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
        <StatsStageFunnel />
        <StatsPartyBars />
        <StatsCategoryDonut />
        <StatsTrend />
      </div>
    </div>
  );
}
