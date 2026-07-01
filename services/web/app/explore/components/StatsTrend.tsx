'use client';

import { useGetStatisticsTrend } from '../apis';

const WIDTH = 320;
const HEIGHT = 130;
const PAD = 10;
const BASELINE = HEIGHT - 20;

/** 월별 발의 추이 라인/에어리어(순수 SVG). */
export default function StatsTrend() {
  const { data } = useGetStatisticsTrend(6);
  const points = data?.data ?? [];

  if (points.length === 0) return null;

  const max = Math.max(...points.map((p) => p.count), 1);
  const n = points.length;
  const x = (i: number) => (n === 1 ? WIDTH / 2 : PAD + (i * (WIDTH - 2 * PAD)) / (n - 1));
  const y = (v: number) => BASELINE - (v / max) * (HEIGHT - 40);

  const line = points.map((p, i) => `${i === 0 ? 'M' : 'L'}${x(i).toFixed(1)},${y(p.count).toFixed(1)}`).join(' ');
  const area = `${line} L${x(n - 1).toFixed(1)},${BASELINE} L${x(0).toFixed(1)},${BASELINE} Z`;
  const last = points[n - 1];

  return (
    <div className="rounded-2xl border border-gray-1 bg-white p-4 shadow-sm dark:border-dark-l dark:bg-dark-b">
      <div className="mb-1 flex items-baseline justify-between">
        <h2 className="text-[14px] font-bold text-primary-3 dark:text-gray-0.5">월별 발의 추이</h2>
        <span className="text-[12px] text-gray-2">최근 {n}개월</span>
      </div>
      <svg
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
        className="w-full"
        preserveAspectRatio="none"
        role="img"
        aria-label="월별 발의 추이 그래프">
        <defs>
          <linearGradient id="statTrendArea" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#0088ff" stopOpacity="0.22" />
            <stop offset="100%" stopColor="#0088ff" stopOpacity="0" />
          </linearGradient>
        </defs>
        <path d={area} fill="url(#statTrendArea)" />
        <path d={line} fill="none" stroke="#0088ff" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
        <circle cx={x(n - 1)} cy={y(last.count)} r="4" fill="#0088ff" stroke="#fff" strokeWidth="2" />
      </svg>
      <div className="mt-1 flex justify-between px-1 text-[10px] text-gray-2">
        {points.map((p) => (
          <span key={p.month}>{Number(p.month.slice(5))}월</span>
        ))}
      </div>
    </div>
  );
}
