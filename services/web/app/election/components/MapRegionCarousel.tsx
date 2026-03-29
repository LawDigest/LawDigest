'use client';

import { useState, useRef, useCallback } from 'react';
import KoreaMap, { MAP_REGIONS, ELECTION_INFO } from './KoreaMap';
import type { CentroidInfo } from './KoreaMap';
import ProvinceInfoCard from './ProvinceInfoCard';
import { MOCK_POLL_DATA } from '../data/mockPollData';

interface LeaderLine {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  color: string;
}

/** centroid x 기준으로 시도를 좌/우 사이드바에 분배 */
function splitProvinces(provinces: string[], centroids: CentroidInfo[]): { left: string[]; right: string[] } {
  if (provinces.length === 0) return { left: [], right: [] };

  const centroidMap = new Map(centroids.map((c) => [c.provinceName, c.x]));
  const unique = provinces.filter((p, i) => provinces.indexOf(p) === i);

  const withX = unique
    .filter((p) => ELECTION_INFO[p] != null)
    .map((p) => ({ name: p, x: centroidMap.get(p) ?? 9999 }))
    .sort((a, b) => a.x - b.x);

  const half = Math.ceil(withX.length / 2);
  return {
    left: withX.slice(0, half).map((p) => p.name),
    right: withX.slice(half).map((p) => p.name),
  };
}

const MAP_HEIGHT = 280;

export default function MapRegionCarousel() {
  const [regionIndex, setRegionIndex] = useState(0);
  const [centroids, setCentroids] = useState<CentroidInfo[]>([]);
  const region = MAP_REGIONS[regionIndex];

  const containerRef = useRef<HTMLDivElement>(null);
  const cardRefs = useRef<Map<string, HTMLDivElement>>(new Map());

  const handleCentroidsReady = useCallback((incoming: CentroidInfo[]) => {
    setCentroids(incoming);
  }, []);

  // 표시할 시도 목록 (중복 제거 + ELECTION_INFO 존재 여부 필터)
  const allProvinces = (region.provinces ?? []).filter((p, i, arr) => arr.indexOf(p) === i && ELECTION_INFO[p] != null);

  // centroid가 있으면 x 기준 분배, 없으면 단순 반분
  const { left: leftProvinces, right: rightProvinces } =
    centroids.length > 0
      ? splitProvinces(allProvinces, centroids)
      : {
          left: allProvinces.slice(0, Math.ceil(allProvinces.length / 2)),
          right: allProvinces.slice(Math.ceil(allProvinces.length / 2)),
        };

  // 지시선 계산 (centroid 준비 후 DOM 위치 기반)
  const leaderLines: LeaderLine[] = [];
  if (centroids.length > 0 && containerRef.current) {
    const containerRect = containerRef.current.getBoundingClientRect();

    const computeLines = (provinces: string[], side: 'left' | 'right') => {
      provinces.forEach((pName) => {
        const cardEl = cardRefs.current.get(pName);
        const centroid = centroids.find((c) => c.provinceName === pName);
        if (!cardEl || !centroid) return;

        const cardRect = cardEl.getBoundingClientRect();
        const x1 = side === 'left' ? cardRect.right - containerRect.left : cardRect.left - containerRect.left;
        const y1 = (cardRect.top + cardRect.bottom) / 2 - containerRect.top;

        const info = ELECTION_INFO[pName];
        const poll = MOCK_POLL_DATA[pName];
        const c1Leads = !poll || poll.c1Pct >= poll.c2Pct;
        const color = c1Leads ? info?.c1.color ?? '#999' : info?.c2.color ?? '#999';

        leaderLines.push({ x1, y1, x2: centroid.x, y2: centroid.y, color });
      });
    };

    computeLines(leftProvinces, 'left');
    computeLines(rightProvinces, 'right');
  }

  const showSidebars = regionIndex !== 0 && region.provinces !== null;

  return (
    <div className="flex flex-col gap-3">
      {/* 지도 + 사이드바 컨테이너 */}
      <div ref={containerRef} className="relative w-full" style={{ height: MAP_HEIGHT }}>
        {/* 지도 */}
        <KoreaMap
          regionIndex={regionIndex}
          onRegionChange={(idx) => {
            setRegionIndex(idx);
            setCentroids([]); // 권역 변경 시 지시선 초기화
          }}
          onCentroidsReady={handleCentroidsReady}
        />

        {/* 좌 사이드바 */}
        {showSidebars && leftProvinces.length > 0 && (
          <div className="absolute left-1 top-0 h-full flex flex-col justify-around pointer-events-none z-10">
            {leftProvinces.map((pName) => {
              const info = ELECTION_INFO[pName];
              if (!info) return null;
              return (
                <ProvinceInfoCard
                  key={pName}
                  ref={(el) => {
                    if (el) cardRefs.current.set(pName, el);
                    else cardRefs.current.delete(pName);
                  }}
                  provinceName={pName}
                  info={info}
                  side="left"
                />
              );
            })}
          </div>
        )}

        {/* 우 사이드바 */}
        {showSidebars && rightProvinces.length > 0 && (
          <div className="absolute right-1 top-0 h-full flex flex-col justify-around pointer-events-none z-10">
            {rightProvinces.map((pName) => {
              const info = ELECTION_INFO[pName];
              if (!info) return null;
              return (
                <ProvinceInfoCard
                  key={pName}
                  ref={(el) => {
                    if (el) cardRefs.current.set(pName, el);
                    else cardRefs.current.delete(pName);
                  }}
                  provinceName={pName}
                  info={info}
                  side="right"
                />
              );
            })}
          </div>
        )}

        {/* 지시선 overlay SVG */}
        {showSidebars && leaderLines.length > 0 && (
          <svg
            className="absolute inset-0 pointer-events-none z-20"
            width="100%"
            height={MAP_HEIGHT}
            style={{ overflow: 'visible' }}>
            {leaderLines.map((line) => {
              const cpx = (line.x1 + line.x2) / 2;
              return (
                <path
                  key={`${line.x1}-${line.y1}-${line.x2}-${line.y2}`}
                  d={`M${line.x1},${line.y1} C${cpx},${line.y1} ${cpx},${line.y2} ${line.x2},${line.y2}`}
                  fill="none"
                  stroke={line.color}
                  strokeWidth={1.2}
                  strokeDasharray="3,2"
                  opacity={0.65}
                />
              );
            })}
          </svg>
        )}
      </div>

      {/* 권역 라벨 + 페이지 인디케이터 */}
      <div className="flex items-center justify-between px-1">
        <div className="flex items-center gap-2">
          <span className="text-sm font-bold text-gray-4 dark:text-white">{region.label}</span>
          <span className="text-xs text-gray-2">
            {regionIndex === 0 ? '전국' : `${regionIndex} / ${MAP_REGIONS.length - 1}`}
          </span>
        </div>
        {/* 도트 인디케이터 */}
        <div className="flex items-center gap-1">
          {MAP_REGIONS.map((r, i) => (
            <button
              key={r.key}
              type="button"
              aria-label={r.label}
              onClick={() => {
                setRegionIndex(i);
                setCentroids([]);
              }}
              className={[
                'rounded-full transition-all',
                i === regionIndex ? 'w-4 h-1.5 bg-gray-4 dark:bg-white' : 'w-1.5 h-1.5 bg-gray-1 dark:bg-dark-l',
              ].join(' ')}
            />
          ))}
        </div>
      </div>

      {/* 스와이프 힌트 */}
      {regionIndex === 0 && (
        <p className="text-center text-xs text-gray-2 opacity-60">← 좌우로 밀어 권역을 이동하세요 →</p>
      )}
    </div>
  );
}
