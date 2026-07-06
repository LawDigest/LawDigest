'use client';

import { useMemo } from 'react';
import { getPartyColor } from '@/constants/party';
import { useGetParliamentaryParties } from '../apis';
import { buildHemicycle } from '../lib/hemicycle';

const VIEW_W = 100;
const VIEW_H = 54;
const CENTER_X = VIEW_W / 2;
const CENTER_Y = VIEW_H - 2;
const OUTER_R = 46;

/** 제22대 국회 의석 분포 — 본회의장 좌석을 형상화한 반원형 좌석도. */
export default function SeatDistribution() {
  const { data } = useGetParliamentaryParties();
  const parties = useMemo(
    () => [...(data?.data ?? [])].sort((a, b) => b.congressman_count - a.congressman_count),
    [data],
  );
  const total = parties.reduce((sum, p) => sum + p.congressman_count, 0);

  // 좌석 좌표 + 각 좌석에 배정된 정당 색을 계산한다.
  const { seats, rowGap } = useMemo(() => buildHemicycle(total), [total]);
  const seatColors = useMemo(() => {
    const colors: string[] = [];
    parties.forEach((party) => {
      const color = getPartyColor(party.party_name);
      for (let i = 0; i < party.congressman_count; i += 1) colors.push(color);
    });
    return colors;
  }, [parties]);

  if (total === 0) return null;

  // 좌석 원 반지름: 행 간격의 약 40%, 과대/과소 방지로 clamp.
  const seatR = Math.max(0.9, Math.min(1.9, OUTER_R * rowGap * 0.4));

  return (
    <section className="rounded-2xl border border-gray-1 bg-white p-4 shadow-sm dark:border-dark-l dark:bg-dark-b">
      <div className="mb-1 flex items-baseline justify-between">
        <h2 className="text-[14px] font-bold text-primary-3 dark:text-gray-0.5">제22대 국회 의석 분포</h2>
        <span className="text-[12px] text-gray-2">재적 {total.toLocaleString()}석</span>
      </div>

      <div className="relative">
        <svg
          viewBox={`0 0 ${VIEW_W} ${VIEW_H}`}
          className="mx-auto block w-full max-w-[420px]"
          role="img"
          aria-label={`제22대 국회 재적 ${total}석 의석 분포도`}>
          {seats.map((seat, index) => {
            const r = OUTER_R * seat.radius;
            const cx = CENTER_X + r * Math.cos(seat.theta);
            const cy = CENTER_Y - r * Math.sin(seat.theta);
            return (
              <circle
                key={`${seat.row}-${seat.theta}`}
                cx={cx}
                cy={cy}
                r={seatR}
                fill={seatColors[index] ?? getPartyColor(null)}
              />
            );
          })}
        </svg>
        {/* 반원 중앙의 재적 수 표기 */}
        <div className="pointer-events-none absolute inset-x-0 bottom-1 flex flex-col items-center">
          <span className="text-[20px] font-extrabold leading-none text-primary-3 dark:text-gray-0.5">
            {total.toLocaleString()}
          </span>
          <span className="text-[10px] text-gray-2">재적 의석</span>
        </div>
      </div>

      <div className="mt-3 flex flex-wrap justify-center gap-x-4 gap-y-1.5 text-[12px] text-gray-3 dark:text-gray-1">
        {parties.map((party) => (
          <span key={party.party_id} className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full" style={{ background: getPartyColor(party.party_name) }} />
            {party.party_name} {party.congressman_count.toLocaleString()}
          </span>
        ))}
      </div>
    </section>
  );
}
