'use client';

import { useState, useRef, useCallback } from 'react';
import KoreaMap, { MAP_REGIONS, ELECTION_INFO } from './KoreaMap';
import type { CentroidInfo, RegionCentroidInfo } from './KoreaMap';
import ProvinceInfoCard from './ProvinceInfoCard';
import { MOCK_POLL_DATA } from '../data/mockPollData';

interface LeaderLine {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  color: string;
  side: 'left' | 'right';
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

/** x 기준으로 항목을 좌/우로 분배 */
function splitByX<T extends { x: number }>(items: T[]): { left: T[]; right: T[] } {
  const sorted = [...items].sort((a, b) => a.x - b.x);
  const half = Math.ceil(sorted.length / 2);
  return { left: sorted.slice(0, half), right: sorted.slice(half) };
}

/** 지시선 path 계산: 수평 후 대각선, bend는 항상 카드 바깥 방향 */
function leaderLinePath(line: LeaderLine): string {
  const rawBend = line.x1 + (line.x2 - line.x1) * 0.45;
  const bendX = line.side === 'left' ? Math.max(line.x1, rawBend) : Math.min(line.x1, rawBend);
  return `M${line.x1},${line.y1} H${bendX} L${line.x2},${line.y2}`;
}

const MAP_HEIGHT = 280;

export default function MapRegionCarousel() {
  const [regionIndex, setRegionIndex] = useState(0);
  const [centroids, setCentroids] = useState<CentroidInfo[]>([]);
  const [regionCentroids, setRegionCentroids] = useState<RegionCentroidInfo[]>([]);
  const region = MAP_REGIONS[regionIndex];

  const containerRef = useRef<HTMLDivElement>(null);
  const cardRefs = useRef<Map<string, HTMLDivElement>>(new Map());
  const regionLabelRefs = useRef<Map<number, HTMLButtonElement>>(new Map());

  const handleCentroidsReady = useCallback((incoming: CentroidInfo[]) => {
    setCentroids(incoming);
  }, []);

  const handleRegionCentroidsReady = useCallback((incoming: RegionCentroidInfo[]) => {
    setRegionCentroids(incoming);
  }, []);

  const goToRegion = useCallback((idx: number) => {
    setRegionIndex(idx);
    setCentroids([]);
    setRegionCentroids([]);
  }, []);

  // ── 시도 분배 ────────────────────────────────────────────────────────────────
  const allProvinces = (region.provinces ?? []).filter((p, i, arr) => arr.indexOf(p) === i && ELECTION_INFO[p] != null);

  const { left: leftProvinces, right: rightProvinces } =
    centroids.length > 0
      ? splitProvinces(allProvinces, centroids)
      : {
          left: allProvinces.slice(0, Math.ceil(allProvinces.length / 2)),
          right: allProvinces.slice(Math.ceil(allProvinces.length / 2)),
        };

  // ── 권역 분배 ────────────────────────────────────────────────────────────────
  const { left: leftRegions, right: rightRegions } = splitByX(regionCentroids);

  // ── 지시선 계산 ──────────────────────────────────────────────────────────────
  const leaderLines: LeaderLine[] = [];
  const regionLeaderLines: LeaderLine[] = [];

  if (containerRef.current) {
    const containerRect = containerRef.current.getBoundingClientRect();

    // 시도 지시선
    if (centroids.length > 0) {
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

          leaderLines.push({ x1, y1, x2: centroid.x, y2: centroid.y, color, side });
        });
      };
      computeLines(leftProvinces, 'left');
      computeLines(rightProvinces, 'right');
    }

    // 권역 지시선
    if (regionCentroids.length > 0) {
      const computeRegionLines = (regions: RegionCentroidInfo[], side: 'left' | 'right') => {
        regions.forEach((rInfo) => {
          const labelEl = regionLabelRefs.current.get(rInfo.regionIndex);
          if (!labelEl) return;
          const labelRect = labelEl.getBoundingClientRect();
          const x1 = side === 'left' ? labelRect.right - containerRect.left : labelRect.left - containerRect.left;
          const y1 = (labelRect.top + labelRect.bottom) / 2 - containerRect.top;
          regionLeaderLines.push({ x1, y1, x2: rInfo.x, y2: rInfo.y, color: '#9CA3AF', side });
        });
      };
      computeRegionLines(leftRegions, 'left');
      computeRegionLines(rightRegions, 'right');
    }
  }

  const showSidebars = regionIndex !== 0 && region.provinces !== null;
  const showRegionShortcuts = regionIndex === 0 && regionCentroids.length > 0;

  return (
    <div className="flex flex-col gap-3">
      {/* 지도 + 오버레이 컨테이너 */}
      <div ref={containerRef} className="relative w-full" style={{ height: MAP_HEIGHT }}>
        {/* 지도 */}
        <KoreaMap
          regionIndex={regionIndex}
          onRegionChange={goToRegion}
          onCentroidsReady={handleCentroidsReady}
          onRegionCentroidsReady={handleRegionCentroidsReady}
        />

        {/* 시도 좌 사이드바 */}
        {showSidebars && leftProvinces.length > 0 && (
          <div className="absolute left-1 top-0 h-full flex flex-col justify-around pointer-events-none z-10 animate-fade-in">
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

        {/* 시도 우 사이드바 */}
        {showSidebars && rightProvinces.length > 0 && (
          <div className="absolute right-1 top-0 h-full flex flex-col justify-around pointer-events-none z-10 animate-fade-in">
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

        {/* 전국 뷰 돌아가기 버튼 */}
        {regionIndex !== 0 && (
          <button
            type="button"
            onClick={() => goToRegion(0)}
            className="absolute top-1.5 left-1/2 -translate-x-1/2 z-30 pointer-events-auto text-[9px] font-medium text-gray-500 bg-white/80 backdrop-blur-sm rounded-full px-2.5 py-0.5 animate-fade-up">
            ← 전국
          </button>
        )}

        {/* 권역 바로가기 좌 */}
        {showRegionShortcuts && leftRegions.length > 0 && (
          <div className="absolute left-1 top-0 h-full flex flex-col justify-around pointer-events-none z-10 animate-fade-in">
            {leftRegions.map((rInfo) => (
              <button
                key={rInfo.regionIndex}
                ref={(el) => {
                  if (el) regionLabelRefs.current.set(rInfo.regionIndex, el);
                  else regionLabelRefs.current.delete(rInfo.regionIndex);
                }}
                type="button"
                onClick={() => goToRegion(rInfo.regionIndex)}
                className="pointer-events-auto bg-white/85 backdrop-blur-sm rounded px-1.5 py-1 text-left leading-tight">
                <span className="block text-sm font-bold text-gray-800">{rInfo.label}</span>
                {rInfo.leadingPct > 0 && (
                  <span className="block text-[10px] font-semibold" style={{ color: rInfo.leadingColor }}>
                    {rInfo.leadingParty} {rInfo.leadingPct.toFixed(1)}%
                  </span>
                )}
              </button>
            ))}
          </div>
        )}

        {/* 권역 바로가기 우 */}
        {showRegionShortcuts && rightRegions.length > 0 && (
          <div className="absolute right-1 top-0 h-full flex flex-col justify-around pointer-events-none z-10 animate-fade-in">
            {rightRegions.map((rInfo) => (
              <button
                key={rInfo.regionIndex}
                ref={(el) => {
                  if (el) regionLabelRefs.current.set(rInfo.regionIndex, el);
                  else regionLabelRefs.current.delete(rInfo.regionIndex);
                }}
                type="button"
                onClick={() => goToRegion(rInfo.regionIndex)}
                className="pointer-events-auto bg-white/85 backdrop-blur-sm rounded px-1.5 py-1 text-right leading-tight">
                <span className="block text-sm font-bold text-gray-800">{rInfo.label}</span>
                {rInfo.leadingPct > 0 && (
                  <span className="block text-[10px] font-semibold" style={{ color: rInfo.leadingColor }}>
                    {rInfo.leadingParty} {rInfo.leadingPct.toFixed(1)}%
                  </span>
                )}
              </button>
            ))}
          </div>
        )}

        {/* 지시선 overlay SVG */}
        {(leaderLines.length > 0 || regionLeaderLines.length > 0) && (
          <svg
            className="absolute inset-0 pointer-events-none z-20 animate-fade-in"
            width="100%"
            height={MAP_HEIGHT}
            style={{ overflow: 'visible' }}>
            {/* 권역 지시선 */}
            {regionLeaderLines.map((line) => (
              <path
                key={`r-${line.x1}-${line.y1}-${line.x2}-${line.y2}`}
                d={leaderLinePath(line)}
                fill="none"
                stroke={line.color}
                strokeWidth={1.0}
                strokeDasharray="3,2"
                opacity={0.55}
              />
            ))}
            {/* 시도 지시선 */}
            {leaderLines.map((line) => (
              <path
                key={`${line.x1}-${line.y1}-${line.x2}-${line.y2}`}
                d={leaderLinePath(line)}
                fill="none"
                stroke={line.color}
                strokeWidth={1.2}
                strokeDasharray="3,2"
                opacity={0.7}
              />
            ))}
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
              onClick={() => goToRegion(i)}
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
