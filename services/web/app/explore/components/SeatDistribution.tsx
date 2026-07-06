'use client';

import { useMemo, useRef, useState } from 'react';
import Image from 'next/image';
import { motion } from 'framer-motion';
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

// 직사각형(포커스) 배치 영역.
const RECT_PAD_X = 5;
const RECT_PAD_Y = 5;

// 좌석 이동과 패널 폭 전환(CSS)을 같은 duration·easing으로 맞춰 한 번의 애니메이션처럼 보이게 한다.
const DOT_DURATION = 0.7;
const dotTransition = (index: number) => ({
  type: 'tween' as const,
  ease: [0.4, 0, 0.2, 1] as const,
  duration: DOT_DURATION,
  delay: Math.min(index * 0.0005, 0.16),
});

/** 제22대 국회 의석 분포 — 기본은 반원 좌석도, 정당 클릭 시 좌석이 직사각형으로 정렬되고 정당 상세가 표시된다. */
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

  // 반원 좌표.
  const hemiPositions = useMemo(
    () =>
      seats.map((seat) => ({
        x: CENTER_X + OUTER_R * seat.radius * Math.cos(seat.theta),
        y: CENTER_Y - OUTER_R * seat.radius * Math.sin(seat.theta),
      })),
    [seats],
  );

  // 직사각형(포커스) 좌표 — 정당 순서대로 행 우선 채움.
  const rect = useMemo(() => {
    const usableW = VIEW_W - RECT_PAD_X * 2;
    const usableH = VIEW_H - RECT_PAD_Y * 2;
    const cols = Math.max(1, Math.round(Math.sqrt(total * (usableW / usableH))));
    const rows = Math.max(1, Math.ceil(total / cols));
    const sx = usableW / cols;
    const sy = usableH / rows;
    const r = Math.max(0.8, Math.min(sx, sy) * 0.36);
    const positions = seats.map((_, i) => ({
      x: RECT_PAD_X + sx * ((i % cols) + 0.5),
      y: RECT_PAD_Y + sy * (Math.floor(i / cols) + 0.5),
    }));
    return { positions, r };
  }, [seats, total]);

  if (total === 0) return null;

  const hemiR = Math.max(1, Math.min(1.9, OUTER_R * rowGap * 0.4));
  const isFocused = focusedId != null;
  const focusedParty = focusedId != null ? partyById.get(focusedId) : undefined;
  const hoveredParty = hovered ? partyById.get(hovered.partyId) : undefined;
  const majoritySeat = seats[Math.min(majority, seats.length) - 1];

  const handleSeatMove = (event: React.MouseEvent, partyId: number) => {
    const rectBox = chartRef.current?.getBoundingClientRect();
    if (!rectBox) return;
    setHovered({ partyId, x: event.clientX - rectBox.left, y: event.clientY - rectBox.top });
  };

  const seatOpacity = (partyId: number) => {
    if (isFocused) return partyId === focusedId ? 1 : 0.14;
    if (hovered) return partyId === hovered.partyId ? 1 : 0.4;
    return 1;
  };

  const toggleFocus = (partyId: number) => setFocusedId((prev) => (prev === partyId ? null : partyId));

  return (
    <section className="rounded-2xl border border-gray-1 bg-white p-4 shadow-sm dark:border-dark-l dark:bg-dark-b">
      <div className="mb-2 flex items-baseline justify-between">
        <h2 className="text-[14px] font-bold text-primary-3 dark:text-gray-0.5">제22대 국회 의석 분포</h2>
        <span className="text-[12px] text-gray-2">
          재적 {total.toLocaleString()}석 · 과반 {majority.toLocaleString()}석
        </span>
      </div>

      <div className="flex flex-col items-center md:flex-row md:items-center md:justify-center">
        {/* 좌석 차트 (기본 반원, 포커스 시 왼쪽 직사각형) */}
        <div ref={chartRef} className="relative w-full min-w-0 max-w-[420px]" onMouseLeave={() => setHovered(null)}>
          <svg
            viewBox={`0 0 ${VIEW_W} ${VIEW_H}`}
            className="block w-full"
            role="img"
            aria-label={`제22대 국회 재적 ${total}석 의석 분포도`}>
            {seats.map((seat, index) => {
              const partyId = seatPartyIds[index];
              const party = partyById.get(partyId);
              const target = isFocused ? rect.positions[index] : hemiPositions[index];
              return (
                <motion.circle
                  key={`${seat.row}-${seat.theta}`}
                  initial={false}
                  animate={{ cx: target.x, cy: target.y, r: isFocused ? rect.r : hemiR, opacity: seatOpacity(partyId) }}
                  transition={dotTransition(index)}
                  fill={getPartyColor(party?.party_name)}
                  className="cursor-pointer"
                  onMouseEnter={(event) => handleSeatMove(event, partyId)}
                  onMouseMove={(event) => handleSeatMove(event, partyId)}
                  onClick={() => toggleFocus(partyId)}
                />
              );
            })}

            {/* 과반선(반원 상태에서만) */}
            {!isFocused &&
              majoritySeat &&
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

          {/* 반원 중앙 재적 수 (반원 상태에서만) */}
          {!isFocused && (
            <div className="pointer-events-none absolute inset-x-0 bottom-1 flex flex-col items-center">
              <span className="text-[20px] font-extrabold leading-none text-primary-3 dark:text-gray-0.5">
                {total.toLocaleString()}
              </span>
              <span className="text-[10px] text-gray-2">재적 의석</span>
            </div>
          )}

          {/* hover 툴팁 (좌석 hover 시에만 커서 위치에 표시) */}
          {hoveredParty && hovered && hovered.x >= 0 && (
            <div
              className="pointer-events-none absolute z-20 -translate-x-1/2 -translate-y-full whitespace-nowrap rounded-md bg-primary-3 px-2 py-1 text-[11px] font-semibold text-white shadow-md dark:bg-gray-0.5 dark:text-black"
              style={{ left: hovered.x, top: hovered.y - 6 }}>
              {hoveredParty.party_name} {hoveredParty.congressman_count.toLocaleString()}석
            </div>
          )}
        </div>

        {/* 포커스 정당 상세 — 항상 렌더링하고 폭/높이만 CSS로 전환해 차트 축소와 한 번의 애니메이션으로 이어지게 한다. */}
        <div
          className={`shrink-0 overflow-hidden transition-all duration-700 ease-[cubic-bezier(0.4,0,0.2,1)] ${
            focusedParty ? 'mt-3 max-h-[320px] md:mt-0 md:ml-4 md:w-[200px]' : 'mt-0 max-h-0 md:w-0'
          }`}>
          <div className="w-full md:w-[200px]">
            {focusedParty && (
              <motion.div
                key={focusedId}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.35, delay: 0.15 }}
                className="relative">
                <button
                  type="button"
                  onClick={() => setFocusedId(null)}
                  aria-label="정당 포커스 해제"
                  className="absolute right-0 top-0 grid h-7 w-7 place-items-center rounded-full text-gray-2 hover:bg-gray-0.5 dark:hover:bg-dark-l">
                  <span className="material-symbols-outlined text-[18px]">close</span>
                </button>

                <div className="flex items-center justify-between gap-2 pr-8">
                  <div className="flex min-w-0 items-center gap-2">
                    {(() => {
                      const logoSrc = getPartyLogoSrc(focusedParty.party_image_url, isDark);
                      // 가로형 정당 로고는 이름을 포함하므로 원형 크롭 없이 전체 로고만 표시한다.
                      return logoSrc ? (
                        <Image
                          src={logoSrc}
                          alt={`${focusedParty.party_name} 로고`}
                          width={88}
                          height={32}
                          className="h-8 w-auto max-w-[88px] shrink-0 object-contain object-left"
                        />
                      ) : (
                        <>
                          <span
                            className="grid h-9 w-9 shrink-0 place-items-center rounded-full text-[13px] font-bold text-white"
                            style={{ background: getPartyColor(focusedParty.party_name) }}>
                            {focusedParty.party_name.trim().charAt(0)}
                          </span>
                          <span className="truncate text-[14px] font-bold text-primary-3 dark:text-gray-0.5">
                            {focusedParty.party_name}
                          </span>
                        </>
                      );
                    })()}
                  </div>
                  <div className="text-right">
                    <div className="text-[11px] text-gray-2">의석수</div>
                    <div className="text-[18px] font-extrabold leading-tight text-primary-3 dark:text-gray-0.5">
                      {focusedParty.congressman_count.toLocaleString()}석
                    </div>
                  </div>
                </div>

                <div className="mt-3 flex flex-col gap-2 text-[13px]">
                  <div className="flex items-center justify-between">
                    <span className="text-gray-2">의석 비율</span>
                    <span className="font-bold text-primary-3 dark:text-gray-0.5">
                      {((focusedParty.congressman_count / total) * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-gray-2">발의 법안</span>
                    <span className="font-bold text-primary-3 dark:text-gray-0.5">
                      {(billCountById.get(focusedParty.party_id) ?? 0).toLocaleString()}건
                    </span>
                  </div>
                </div>
              </motion.div>
            )}
          </div>
        </div>
      </div>

      {/* 정당 범례 (클릭 시 포커스 토글, hover 시 강조) */}
      <div className="mt-3 flex flex-wrap justify-center gap-x-3 gap-y-1.5 text-[12px] text-gray-3 dark:text-gray-1">
        {parties.map((party) => {
          const active = focusedId === party.party_id;
          return (
            <button
              key={party.party_id}
              type="button"
              onClick={() => toggleFocus(party.party_id)}
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
