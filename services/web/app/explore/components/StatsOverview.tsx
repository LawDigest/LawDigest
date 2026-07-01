'use client';

import { useGetStatisticsOverview } from '../apis';

/** KPI 카드 4종 — 총 발의 / 가결 / 계류 중 / 가결률. */
export default function StatsOverview() {
  const { data } = useGetStatisticsOverview();
  const overview = data?.data;

  if (!overview) return null;

  const cards = [
    { label: '총 발의', value: overview.total_count.toLocaleString(), unit: '건' },
    { label: '가결', value: overview.passed_count.toLocaleString(), unit: '건' },
    { label: '계류 중', value: overview.pending_count.toLocaleString(), unit: '건' },
    { label: '가결률', value: overview.pass_rate.toLocaleString(), unit: '%' },
  ];

  return (
    <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
      {cards.map((card) => (
        <div
          key={card.label}
          className="rounded-2xl border border-gray-1 bg-white p-4 shadow-sm dark:border-dark-l dark:bg-dark-b">
          <p className="text-[12px] text-gray-2">{card.label}</p>
          <p className="mt-1 text-[24px] font-bold leading-none text-primary-3 dark:text-gray-0.5">
            {card.value}
            <span className="ml-0.5 text-[13px] font-medium text-gray-2">{card.unit}</span>
          </p>
        </div>
      ))}
    </div>
  );
}
