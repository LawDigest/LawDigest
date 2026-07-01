'use client';

import { StatisticsStage, useGetStatisticsStage } from '../apis';

const STAGES: { key: keyof StatisticsStage; label: string; color: string }[] = [
  { key: 'receipt_count', label: '접수', color: '#96BCFA' },
  { key: 'committee_count', label: '위원회 심사', color: '#5C8DEB' },
  { key: 'plenary_count', label: '본회의 심의', color: '#2D5BC0' },
  { key: 'promulgated_count', label: '공포', color: '#152484' },
];

/** 입법 진행 단계 퍼널 — 접수 대비 누적 도달 비율. */
export default function StatsStageFunnel() {
  const { data } = useGetStatisticsStage();
  const stage = data?.data;

  if (!stage) return null;

  const base = stage.receipt_count || 1;

  return (
    <div className="rounded-2xl border border-gray-1 bg-white p-4 shadow-sm dark:border-dark-l dark:bg-dark-b">
      <h2 className="mb-3 text-[14px] font-bold text-primary-3 dark:text-gray-0.5">입법 진행 단계</h2>
      <div className="space-y-2">
        {STAGES.map(({ key, label, color }) => {
          const value = stage[key];
          const pct = Math.round((value / base) * 100);
          return (
            <div key={key}>
              <div className="mb-1 flex justify-between text-[12px]">
                <span className="font-medium text-primary-3 dark:text-gray-0.5">{label}</span>
                <span className="text-gray-2">
                  {value.toLocaleString()}건 · {pct}%
                </span>
              </div>
              <div className="h-7 rounded-lg bg-gray-0.5 dark:bg-dark-l">
                <div className="h-7 rounded-lg" style={{ width: `${pct}%`, background: color }} />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
