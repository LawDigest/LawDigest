'use client';

import { getCategoryMeta } from '@/config/categories';
import { useGetStatisticsByCategory } from '../apis';

const TOP_N = 6;
const ETC_COLOR = '#999999';

/** 분야별 분포 도넛(CSS conic-gradient) + 범례. 상위 N개 + 기타. */
export default function StatsCategoryDonut() {
  const { data } = useGetStatisticsByCategory();
  const raw = (data?.data ?? []).filter((c) => c.category && c.category !== 'unknown');

  if (raw.length === 0) return null;

  const total = raw.reduce((sum, c) => sum + c.count, 0) || 1;
  const top = raw.slice(0, TOP_N);
  const restCount = raw.slice(TOP_N).reduce((sum, c) => sum + c.count, 0);

  const segments = [
    ...top.map((c) => ({
      label: getCategoryMeta(c.category).label,
      color: getCategoryMeta(c.category).color,
      count: c.count,
    })),
    ...(restCount > 0 ? [{ label: '기타', color: ETC_COLOR, count: restCount }] : []),
  ];

  let acc = 0;
  const stops = segments
    .map((seg) => {
      const start = (acc / total) * 100;
      acc += seg.count;
      const end = (acc / total) * 100;
      return `${seg.color} ${start}% ${end}%`;
    })
    .join(', ');

  return (
    <div className="rounded-2xl border border-gray-1 bg-white p-4 shadow-sm dark:border-dark-l dark:bg-dark-b">
      <h2 className="mb-3 text-[14px] font-bold text-primary-3 dark:text-gray-0.5">분야별 분포</h2>
      <div className="flex items-center gap-4">
        <div className="relative h-[112px] w-[112px] shrink-0">
          <div className="h-full w-full rounded-full" style={{ background: `conic-gradient(${stops})` }} />
          <div className="absolute inset-[18px] grid place-items-center rounded-full bg-white text-center dark:bg-dark-b">
            <div>
              <p className="text-[18px] font-bold leading-none text-primary-3 dark:text-gray-0.5">{raw.length}</p>
              <p className="text-[10px] text-gray-2">분야</p>
            </div>
          </div>
        </div>
        <div className="grid flex-1 grid-cols-1 gap-1.5 text-[12px]">
          {segments.map((seg) => (
            <span key={seg.label} className="flex items-center gap-1.5 text-gray-3 dark:text-gray-1">
              <span className="h-2.5 w-2.5 rounded-sm" style={{ background: seg.color }} />
              {seg.label}
              <b className="ml-auto text-primary-3 dark:text-gray-0.5">{Math.round((seg.count / total) * 100)}%</b>
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
