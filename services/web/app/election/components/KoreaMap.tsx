'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import * as d3 from 'd3';
import type { FeatureCollection, Geometry } from 'geojson';

// ─── 권역 정의 ────────────────────────────────────────────────────────────────

export interface MapRegion {
  key: string;
  label: string;
  provinces: string[] | null; // null = 전체
}

export const MAP_REGIONS: MapRegion[] = [
  { key: 'all', label: '전체', provinces: null },
  { key: 'sudogwon', label: '수도권', provinces: ['서울특별시', '인천광역시', '경기도'] },
  {
    key: 'chungcheong',
    label: '충청권',
    provinces: ['대전광역시', '세종특별자치시', '충청북도', '충청남도'],
  },
  {
    key: 'honam',
    label: '호남권',
    provinces: ['광주광역시', '전북특별자치도', '전라북도', '전라남도'],
  },
  { key: 'daegyeong', label: '대경권', provinces: ['대구광역시', '경상북도'] },
  { key: 'dongnam', label: '동남권', provinces: ['부산광역시', '울산광역시', '경상남도'] },
  { key: 'gangwon_jeju', label: '강원/제주', provinces: ['강원특별자치도', '강원도', '제주특별자치도'] },
];

// ─── 컴포넌트 ─────────────────────────────────────────────────────────────────

interface KoreaMapProps {
  regionIndex: number;
  onRegionChange: (index: number) => void;
}

const TRANSITION_DURATION = 600;
const SWIPE_THRESHOLD = 40;

export default function KoreaMap({ regionIndex, onRegionChange }: KoreaMapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const svgRef = useRef<SVGSVGElement>(null);
  const gRef = useRef<SVGGElement | null>(null);
  const projectionRef = useRef<d3.GeoProjection | null>(null);
  const pathRef = useRef<d3.GeoPath | null>(null);
  const geoDataRef = useRef<FeatureCollection<Geometry> | null>(null);
  const [ready, setReady] = useState(false);

  // ── 지도 초기화 ────────────────────────────────────────────────────────────
  useEffect(() => {
    const svg = svgRef.current;
    const container = containerRef.current;
    if (!svg || !container) return;

    const { width, height } = container.getBoundingClientRect();
    const w = width || 320;
    const h = height || 400;

    d3.select(svg).selectAll('*').remove();

    const projection = d3
      .geoMercator()
      .center([127.8, 36.3])
      .scale(w * 5.0)
      .translate([w / 2, h / 2]);

    const path = d3.geoPath().projection(projection);
    projectionRef.current = projection;
    pathRef.current = path;

    const g = d3.select(svg).append('g').attr('class', 'map-root');
    gRef.current = g.node();

    fetch('/geo/korea-provinces.json')
      .then((r) => r.json())
      .then((geo: FeatureCollection<Geometry>) => {
        geoDataRef.current = geo;

        g.selectAll('path')
          .data(geo.features)
          .join('path')
          .attr('d', path as unknown as string)
          .attr('fill', 'white')
          .attr('stroke', '#C8C8C8')
          .attr('stroke-width', 0.8)
          .attr('stroke-linejoin', 'round');

        setReady(true);
      });
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // ── 권역 줌 애니메이션 ──────────────────────────────────────────────────────
  useEffect(() => {
    if (!ready) return;
    const svg = svgRef.current;
    const container = containerRef.current;
    const geo = geoDataRef.current;
    const path = pathRef.current;
    const g = gRef.current;
    if (!svg || !container || !geo || !path || !g) return;

    const { width, height } = container.getBoundingClientRect();
    const w = width || 320;
    const h = height || 400;

    const region = MAP_REGIONS[regionIndex];
    const targetFeatures =
      region.provinces === null
        ? geo.features
        : geo.features.filter((f) =>
            region.provinces!.some((p) => {
              const name: string = (f.properties as Record<string, string>)?.name ?? '';
              return name.includes(p) || p.includes(name);
            }),
          );

    // 선택된 피처들의 경계 계산
    const collection: FeatureCollection<Geometry> = {
      type: 'FeatureCollection',
      features: targetFeatures,
    };

    const bounds = path.bounds(collection as Parameters<typeof path.bounds>[0]);
    const dx = bounds[1][0] - bounds[0][0];
    const dy = bounds[1][1] - bounds[0][1];
    const cx = (bounds[0][0] + bounds[1][0]) / 2;
    const cy = (bounds[0][1] + bounds[1][1]) / 2;

    const padding = region.provinces === null ? 0.85 : 0.7;
    const scale = Math.min((w / dx) * padding, (h / dy) * padding);
    const tx = w / 2 - scale * cx;
    const ty = h / 2 - scale * cy;

    // province 강조: 선택된 권역은 진한 선, 나머지는 연한 선
    d3.select(g)
      .transition()
      .duration(TRANSITION_DURATION)
      .ease(d3.easeCubicInOut)
      .attr('transform', `translate(${tx},${ty}) scale(${scale})`);

    d3.select(g)
      .selectAll<SVGPathElement, (typeof geo.features)[number]>('path')
      .transition()
      .duration(TRANSITION_DURATION)
      .attr('stroke', (f) => {
        if (region.provinces === null) return '#C8C8C8';
        const name: string = (f.properties as Record<string, string>)?.name ?? '';
        const isIn = region.provinces!.some((p) => name.includes(p) || p.includes(name));
        return isIn ? '#3A3A3A' : '#E0E0E0';
      })
      .attr('stroke-width', (f) => {
        if (region.provinces === null) return 0.8 / scale;
        const name: string = (f.properties as Record<string, string>)?.name ?? '';
        const isIn = region.provinces!.some((p) => name.includes(p) || p.includes(name));
        return isIn ? 1.0 / scale : 0.5 / scale;
      })
      .attr('fill', (f) => {
        if (region.provinces === null) return 'white';
        const name: string = (f.properties as Record<string, string>)?.name ?? '';
        const isIn = region.provinces!.some((p) => name.includes(p) || p.includes(name));
        return isIn ? '#F8F9FA' : 'white';
      });
  }, [ready, regionIndex]);

  // ── 스와이프 제스처 ─────────────────────────────────────────────────────────
  const touchStartX = useRef<number | null>(null);
  const pointerStartX = useRef<number | null>(null);

  const goNext = useCallback(
    () => onRegionChange((regionIndex + 1) % MAP_REGIONS.length),
    [regionIndex, onRegionChange],
  );
  const goPrev = useCallback(
    () => onRegionChange((regionIndex - 1 + MAP_REGIONS.length) % MAP_REGIONS.length),
    [regionIndex, onRegionChange],
  );

  const handleTouchStart = useCallback((e: React.TouchEvent) => {
    touchStartX.current = e.touches[0].clientX;
  }, []);

  const handleTouchEnd = useCallback(
    (e: React.TouchEvent) => {
      if (touchStartX.current === null) return;
      const dx = e.changedTouches[0].clientX - touchStartX.current;
      touchStartX.current = null;
      if (dx < -SWIPE_THRESHOLD) goNext();
      else if (dx > SWIPE_THRESHOLD) goPrev();
    },
    [goNext, goPrev],
  );

  const handlePointerDown = useCallback((e: React.PointerEvent) => {
    if (e.pointerType === 'touch') return;
    pointerStartX.current = e.clientX;
  }, []);

  const handlePointerUp = useCallback(
    (e: React.PointerEvent) => {
      if (e.pointerType === 'touch' || pointerStartX.current === null) return;
      const dx = e.clientX - pointerStartX.current;
      pointerStartX.current = null;
      if (dx < -SWIPE_THRESHOLD) goNext();
      else if (dx > SWIPE_THRESHOLD) goPrev();
    },
    [goNext, goPrev],
  );

  return (
    <div
      ref={containerRef}
      className="relative w-full select-none overflow-hidden"
      style={{ touchAction: 'pan-y' }}
      onTouchStart={handleTouchStart}
      onTouchEnd={handleTouchEnd}
      onPointerDown={handlePointerDown}
      onPointerUp={handlePointerUp}>
      <svg
        ref={svgRef}
        className="w-full"
        style={{ height: 280 }}
        viewBox={`0 0 ${containerRef.current?.clientWidth || 320} 280`}
        preserveAspectRatio="xMidYMid meet"
      />
      {!ready && (
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-xs text-gray-2">지도 불러오는 중…</span>
        </div>
      )}
    </div>
  );
}
