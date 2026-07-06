'use client';

import { useMemo, useRef, useState } from 'react';
import { Avatar } from '@nextui-org/avatar';
import { useTheme } from 'next-themes';
import { getPartyColor } from '@/constants/party';
import { getPartyLogoSrc } from '@/utils';
import { ParliamentaryParty, useGetParliamentaryParties, useGetStatisticsByParty } from '../apis';
import { buildHemicycle } from '../lib/hemicycle';
import { orderPartiesByBloc } from '../lib/seatingOrder';

const VIEW_W = 100;
const VIEW_H = 56;
const CENTER_X = VIEW_W / 2;
const CENTER_Y = VIEW_H - 3;
const OUTER_R = 46;

const seatXY = (radius: number, theta: number) => ({
  x: CENTER_X + OUTER_R * radius * Math.cos(theta),
  y: CENTER_Y - OUTER_R * radius * Math.sin(theta),
});

/** 제22대 국회 의석 분포 — 본회의장 좌석을 형상화한 반원형 좌석도(hover 툴팁·클릭 포커스·과반선 포함). */
export default function SeatDistribution() {
  const { theme } = useTheme();
  const isDark = theme === 'dark';
  const { data } = useGetParliamentaryParties();
  const { data: billStats } = useGetStatisticsByParty();

  const parties = useMemo(
    () => [...(data?.data ?? [])].sort((a, b) => b.congressman_count - a.congressman_count),
    [data],
  );
  const total = parties.reduce((sum, p) => sum + p.congressman_count, 0);
  const majority = Math.floor(total / 2) + 1;

  const [focusedId, setFocusedId] = useState<number | null>(null);
  const [hovered, setHovered] = useState<{ partyId: number; x: number; y: number } | null>(null);
  const chartRef = useRef<HTMLDivElement>(null);

  const { seats, rowGap } = useMemo(() => buildHemicycle(total), [total]);

  // 좌석 인덱스 → 정당 id (1위 좌·2위 우·나머지 중앙 순으로 채운다).
  const seatPartyIds = useMemo(() => {
    const ids: number[] = [];
    orderPartiesByBloc(parties).forEach((party) => {
      for (let i = 0; i < party.congressman_count; i += 1) ids.push(party.party_id);
    });
    return ids;
  }, [parties]);

  const partyById = useMemo(() => {
    const map = new Map<number, ParliamentaryParty>();
    parties.forEach((party) => map.set(party.party_id, party));
    return map;
  }, [parties]);

  const billCountById = useMemo(() => {
    const map = new Map<number, number>();
    (billStats?.data ?? []).forEach((row) => map.set(row.party_id, row.count));
    return map;
  }, [billStats]);

  if (total === 0) return null;

  const seatR = Math.max(1, Math.min(1.9, OUTER_R * rowGap * 0.4));
  const focusedParty = focusedId != null ? partyById.get(focusedId) : undefined;
  const hoveredParty = hovered ? partyById.get(hovered.partyId) : undefined;

  // 과반선: 왼쪽부터 majority번째 좌석의 각도에 방사형 점선을 긋는다.
  const majoritySeat = seats[Math.min(majority, seats.length) - 1];

  const handleSeatMove = (event: React.MouseEvent, partyId: number) => {
    const rect = chartRef.current?.getBoundingClientRect();
    if (!rect) return;
    setHovered({ partyId, x: event.clientX - rect.left, y: event.clientY - rect.top });
  };

  const seatOpacity = (partyId: number) => {
    if (focusedId != null) return partyId === focusedId ? 1 : 0.16;
    if (hovered) return partyId === hovered.partyId ? 1 : 0.4;
    return 1;
  };

  return (
    <section className="rounded-2xl border border-gray-1 bg-white p-4 shadow-sm dark:border-dark-l dark:bg-dark-b">
      <div className="mb-2 flex items-baseline justify-between">
        <h2 className="text-[14px] font-bold text-primary-3 dark:text-gray-0.5">제22대 국회 의석 분포</h2>
        <span className="text-[12px] text-gray-2">
          재적 {total.toLocaleString()}석 · 과반 {majority.toLocaleString()}석
        </span>
      </div>

      <div className="flex flex-col gap-4 md:flex-row md:items-center">
        {/* 좌석 차트 */}
        <div ref={chartRef} className="relative md:flex-1" onMouseLeave={() => setHovered(null)}>
          <svg
            viewBox={`0 0 ${VIEW_W} ${VIEW_H}`}
            className="mx-auto block w-full max-w-[420px]"
            role="img"
            aria-label={`제22대 국회 재적 ${total}석 의석 분포도`}>
            {seats.map((seat, index) => {
              const partyId = seatPartyIds[index];
              const party = partyById.get(partyId);
              const { x, y } = seatXY(seat.radius, seat.theta);
              return (
                <circle
                  key={`${seat.row}-${seat.theta}`}
                  cx={x}
                  cy={y}
                  r={seatR}
                  fill={getPartyColor(party?.party_name)}
                  opacity={seatOpacity(partyId)}
                  className="cursor-pointer transition-opacity duration-200"
                  onMouseEnter={(event) => handleSeatMove(event, partyId)}
                  onMouseMove={(event) => handleSeatMove(event, partyId)}
                  onClick={() => setFocusedId((prev) => (prev === partyId ? null : partyId))}
                />
              );
            })}

            {/* 과반선(방사형 점선) */}
            {majoritySeat &&
              (() => {
                const start = {
                  x: CENTER_X + OUTER_R * 0.34 * Math.cos(majoritySeat.theta),
                  y: CENTER_Y - OUTER_R * 0.34 * Math.sin(majoritySeat.theta),
                };
                const end = {
                  x: CENTER_X + (OUTER_R + 4) * Math.cos(majoritySeat.theta),
                  y: CENTER_Y - (OUTER_R + 4) * Math.sin(majoritySeat.theta),
                };
                const anchor = end.x < CENTER_X ? 'end' : 'start';
                return (
                  <g>
                    <line
                      x1={start.x}
                      y1={start.y}
                      x2={end.x}
                      y2={end.y}
                      stroke={isDark ? '#9AA0AA' : '#4B5563'}
                      strokeWidth={0.6}
                      strokeDasharray="1.4 1.2"
                    />
                    <text
                      x={end.x + (anchor === 'end' ? -1 : 1)}
                      y={end.y - 0.5}
                      textAnchor={anchor}
                      fontSize={3.4}
                      fontWeight={700}
                      fill={isDark ? '#C7CBD2' : '#374151'}>
                      과반 {majority}
                    </text>
                  </g>
                );
              })()}
          </svg>

          {/* 반원 중앙 재적 수 */}
          <div className="pointer-events-none absolute inset-x-0 bottom-1 flex flex-col items-center">
            <span className="text-[20px] font-extrabold leading-none text-primary-3 dark:text-gray-0.5">
              {total.toLocaleString()}
            </span>
            <span className="text-[10px] text-gray-2">재적 의석</span>
          </div>

          {/* hover 툴팁 (좌석 hover 시에만 커서 위치에 표시) */}
          {hoveredParty && hovered && hovered.x >= 0 && (
            <div
              className="pointer-events-none absolute z-20 -translate-x-1/2 -translate-y-full whitespace-nowrap rounded-md bg-primary-3 px-2 py-1 text-[11px] font-semibold text-white shadow-md dark:bg-gray-0.5 dark:text-black"
              style={{ left: hovered.x, top: hovered.y - 6 }}>
              {hoveredParty.party_name} {hoveredParty.congressman_count.toLocaleString()}석
            </div>
          )}
        </div>

        {/* 포커스 정당 상세 패널 (모바일 하단 / 데스크톱 우측) */}
        <aside className="md:w-[42%] md:shrink-0">
          {focusedParty ? (
            <div className="rounded-xl border border-gray-1 bg-gray-0.5 p-4 dark:border-dark-l dark:bg-dark-l">
              <div className="flex items-center gap-3">
                <Avatar
                  src={getPartyLogoSrc(focusedParty.party_image_url, isDark) ?? undefined}
                  alt={focusedParty.party_name}
                  showFallback
                  className="h-11 w-11 shrink-0 bg-white ring-2"
                  style={{ '--tw-ring-color': getPartyColor(focusedParty.party_name) } as React.CSSProperties}
                />
                <div className="min-w-0 flex-1">
                  <p className="truncate text-[15px] font-bold text-primary-3 dark:text-gray-0.5">
                    {focusedParty.party_name}
                  </p>
                  <p className="text-[12px] text-gray-2">원내 정당</p>
                </div>
                <button
                  type="button"
                  onClick={() => setFocusedId(null)}
                  aria-label="정당 포커스 해제"
                  className="grid h-7 w-7 place-items-center rounded-full text-gray-2 hover:bg-gray-1 dark:hover:bg-dark-l">
                  <span className="material-symbols-outlined text-[18px]">close</span>
                </button>
              </div>

              <dl className="mt-4 grid grid-cols-3 gap-2 text-center">
                <div className="rounded-lg bg-white px-1 py-2 dark:bg-dark-b">
                  <dt className="text-[11px] text-gray-2">의석수</dt>
                  <dd className="text-[15px] font-bold text-primary-3 dark:text-gray-0.5">
                    {focusedParty.congressman_count.toLocaleString()}
                  </dd>
                </div>
                <div className="rounded-lg bg-white px-1 py-2 dark:bg-dark-b">
                  <dt className="text-[11px] text-gray-2">의석 비율</dt>
                  <dd className="text-[15px] font-bold text-primary-3 dark:text-gray-0.5">
                    {((focusedParty.congressman_count / total) * 100).toFixed(1)}%
                  </dd>
                </div>
                <div className="rounded-lg bg-white px-1 py-2 dark:bg-dark-b">
                  <dt className="text-[11px] text-gray-2">발의 법안</dt>
                  <dd className="text-[15px] font-bold text-primary-3 dark:text-gray-0.5">
                    {(billCountById.get(focusedParty.party_id) ?? 0).toLocaleString()}
                  </dd>
                </div>
              </dl>
            </div>
          ) : (
            <p className="rounded-xl border border-dashed border-gray-1 px-4 py-6 text-center text-[12px] text-gray-2 dark:border-dark-l">
              정당을 클릭하면 의석만 강조되고 상세 정보가 표시됩니다.
            </p>
          )}
        </aside>
      </div>

      {/* 정당 범례 (클릭 시 포커스 토글, hover 시 강조) */}
      <div className="mt-3 flex flex-wrap justify-center gap-x-3 gap-y-1.5 text-[12px] text-gray-3 dark:text-gray-1">
        {parties.map((party) => {
          const active = focusedId === party.party_id;
          return (
            <button
              key={party.party_id}
              type="button"
              onClick={() => setFocusedId((prev) => (prev === party.party_id ? null : party.party_id))}
              onMouseEnter={() => setHovered({ partyId: party.party_id, x: -9999, y: -9999 })}
              onMouseLeave={() => setHovered(null)}
              className={`flex items-center gap-1.5 rounded-full px-2 py-0.5 transition-colors ${
                active ? 'bg-gray-1 dark:bg-dark-l' : 'hover:bg-gray-0.5 dark:hover:bg-dark-l'
              }`}>
              <span className="h-2 w-2 rounded-full" style={{ background: getPartyColor(party.party_name) }} />
              {party.party_name} {party.congressman_count.toLocaleString()}
            </button>
          );
        })}
      </div>
    </section>
  );
}
