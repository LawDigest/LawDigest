'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import * as topojson from 'topojson-client';
import type { FeatureCollection, Feature, Geometry } from 'geojson';
import type {
  Topology,
  GeometryCollection as TopoGeomCollection,
  Polygon as TopoPolygon,
  MultiPolygon as TopoMultiPolygon,
} from 'topojson-specification';
import { MOCK_POLL_DATA } from '../data/mockPollData';

// ─── 상수 ─────────────────────────────────────────────────────────────────────

const TOPO_OBJECT_KEY = 'skorea_provinces_geo';
const TRANSITION_DURATION = 750;
const SWIPE_THRESHOLD = 40;

// ─── 선거 데이터 (제9회 전국동시지방선거 mock – 8회 결과 기준) ─────────────────

export interface CandidateInfo {
  name: string;
  party: string;
  color: string;
}

export interface ProvinceElectionInfo {
  title: string;
  c1: CandidateInfo;
  c2: CandidateInfo;
}

export interface CentroidInfo {
  provinceName: string;
  /** SVG 좌표계 기준 x (줌 변환 적용 후, = 컨테이너 상대 좌표) */
  x: number;
  /** SVG 좌표계 기준 y */
  y: number;
}

export interface RegionCentroidInfo {
  regionIndex: number;
  label: string;
  /** 전국 뷰 기준 화면 좌표 x */
  x: number;
  /** 전국 뷰 기준 화면 좌표 y */
  y: number;
  /** 권역 내 리딩 정당명 */
  leadingParty: string;
  /** 리딩 정당 색상 */
  leadingColor: string;
  /** 권역 내 리딩 정당 평균 득표율 */
  leadingPct: number;
}

export const ELECTION_INFO: Record<string, ProvinceElectionInfo> = {
  서울특별시: {
    title: '서울특별시장',
    c1: { name: '오세훈', party: '국힘', color: '#e61e2b' },
    c2: { name: '송영길', party: '민주', color: '#152484' },
  },
  부산광역시: {
    title: '부산광역시장',
    c1: { name: '박형준', party: '국힘', color: '#e61e2b' },
    c2: { name: '변성완', party: '민주', color: '#152484' },
  },
  대구광역시: {
    title: '대구광역시장',
    c1: { name: '홍준표', party: '국힘', color: '#e61e2b' },
    c2: { name: '서재헌', party: '민주', color: '#152484' },
  },
  인천광역시: {
    title: '인천광역시장',
    c1: { name: '유정복', party: '국힘', color: '#e61e2b' },
    c2: { name: '박남춘', party: '민주', color: '#152484' },
  },
  광주광역시: {
    title: '광주광역시장',
    c1: { name: '강기정', party: '민주', color: '#152484' },
    c2: { name: '김재식', party: '국힘', color: '#e61e2b' },
  },
  대전광역시: {
    title: '대전광역시장',
    c1: { name: '이장우', party: '국힘', color: '#e61e2b' },
    c2: { name: '허태정', party: '민주', color: '#152484' },
  },
  울산광역시: {
    title: '울산광역시장',
    c1: { name: '김두겸', party: '국힘', color: '#e61e2b' },
    c2: { name: '송철호', party: '민주', color: '#152484' },
  },
  세종특별자치시: {
    title: '세종특별자치시장',
    c1: { name: '최민호', party: '국힘', color: '#e61e2b' },
    c2: { name: '이춘희', party: '민주', color: '#152484' },
  },
  경기도: {
    title: '경기도지사',
    c1: { name: '김동연', party: '민주', color: '#152484' },
    c2: { name: '김은혜', party: '국힘', color: '#e61e2b' },
  },
  강원도: {
    title: '강원특별자치도지사',
    c1: { name: '김진태', party: '국힘', color: '#e61e2b' },
    c2: { name: '이광재', party: '민주', color: '#152484' },
  },
  강원특별자치도: {
    title: '강원특별자치도지사',
    c1: { name: '김진태', party: '국힘', color: '#e61e2b' },
    c2: { name: '이광재', party: '민주', color: '#152484' },
  },
  충청북도: {
    title: '충청북도지사',
    c1: { name: '김영환', party: '국힘', color: '#e61e2b' },
    c2: { name: '노영민', party: '민주', color: '#152484' },
  },
  충청남도: {
    title: '충청남도지사',
    c1: { name: '김태흠', party: '국힘', color: '#e61e2b' },
    c2: { name: '양승조', party: '민주', color: '#152484' },
  },
  전라북도: {
    title: '전북특별자치도지사',
    c1: { name: '김관영', party: '민주', color: '#152484' },
    c2: { name: '조배숙', party: '국힘', color: '#e61e2b' },
  },
  전북특별자치도: {
    title: '전북특별자치도지사',
    c1: { name: '김관영', party: '민주', color: '#152484' },
    c2: { name: '조배숙', party: '국힘', color: '#e61e2b' },
  },
  전라남도: {
    title: '전라남도지사',
    c1: { name: '김영록', party: '민주', color: '#152484' },
    c2: { name: '이정현', party: '국힘', color: '#e61e2b' },
  },
  경상북도: {
    title: '경상북도지사',
    c1: { name: '이철우', party: '국힘', color: '#e61e2b' },
    c2: { name: '임미애', party: '민주', color: '#152484' },
  },
  경상남도: {
    title: '경상남도지사',
    c1: { name: '박완수', party: '국힘', color: '#e61e2b' },
    c2: { name: '양문석', party: '민주', color: '#152484' },
  },
  제주특별자치도: {
    title: '제주특별자치도지사',
    c1: { name: '오영훈', party: '민주', color: '#152484' },
    c2: { name: '허향진', party: '국힘', color: '#e61e2b' },
  },
};

// ─── 권역 정의 ────────────────────────────────────────────────────────────────

export interface MapRegion {
  key: string;
  label: string;
  provinces: string[] | null;
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
  {
    key: 'gangwon_jeju',
    label: '강원/제주',
    provinces: ['강원특별자치도', '강원도', '제주특별자치도'],
  },
];

// ─── 헬퍼 ─────────────────────────────────────────────────────────────────────

function isProvinceInRegion(name: string, provinces: string[]): boolean {
  return provinces.some((p) => name.includes(p) || p.includes(name));
}

function getProvinceName(f: Feature<Geometry>): string {
  return (f.properties as Record<string, string>)?.name ?? '';
}

// ─── 컴포넌트 ─────────────────────────────────────────────────────────────────

interface KoreaMapProps {
  regionIndex: number;
  onRegionChange: (index: number) => void;
  onCentroidsReady?: (centroids: CentroidInfo[]) => void;
  onRegionCentroidsReady?: (centroids: RegionCentroidInfo[]) => void;
}

export default function KoreaMap({
  regionIndex,
  onRegionChange,
  onCentroidsReady,
  onRegionCentroidsReady,
}: KoreaMapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const svgRef = useRef<SVGSVGElement>(null);
  const zoomGRef = useRef<SVGGElement | null>(null);
  const outlineElRef = useRef<SVGPathElement | null>(null);
  const labelsGRef = useRef<SVGGElement | null>(null);
  const pathRef = useRef<d3.GeoPath | null>(null);
  const geoRef = useRef<FeatureCollection<Geometry> | null>(null);
  /** 각 권역 index → 사전 계산된 SVG path 문자열 */
  const mergedPathsRef = useRef<Map<number, string>>(new Map());
  /** 시도명 → projection 좌표 centroid */
  const centroidsRef = useRef<Map<string, [number, number]>>(new Map());
  /** 시도명 → projection 좌표 기준 bounding box 면적 */
  const projAreasRef = useRef<Map<string, number>>(new Map());
  const [ready, setReady] = useState(false);

  // ── 초기화 (1회) ───────────────────────────────────────────────────────────
  useEffect(() => {
    const svg = svgRef.current;
    const container = containerRef.current;
    if (!svg || !container) return;

    const { width, height } = container.getBoundingClientRect();
    const w = width || 320;
    const h = height || 280;

    d3.select(svg).selectAll('*').remove();

    const projection = d3
      .geoMercator()
      .center([127.8, 36.3])
      .scale(w * 5.0)
      .translate([w / 2, h / 2]);
    const path = d3.geoPath().projection(projection);
    pathRef.current = path;

    const zoomG = d3.select(svg).append('g').attr('class', 'zoom-layer');
    const labelsG = d3.select(svg).append('g').attr('class', 'labels-layer');
    zoomGRef.current = zoomG.node();
    labelsGRef.current = labelsG.node();

    // 아웃라인 엘리먼트 고정 생성 (d만 교체)
    const outlineEl = zoomG
      .append('path')
      .attr('class', 'region-outline')
      .attr('fill', 'none')
      .attr('stroke', '#2D3748')
      .attr('stroke-linejoin', 'round')
      .attr('pointer-events', 'none')
      .attr('d', '');
    outlineElRef.current = outlineEl.node();

    fetch('/geo/korea-provinces-topo-simple.json')
      .then((r) => r.json())
      .then((topo: Topology) => {
        const fc = topojson.feature(
          topo,
          topo.objects[TOPO_OBJECT_KEY] as TopoGeomCollection,
        ) as FeatureCollection<Geometry>;
        geoRef.current = fc;

        // 시도 path 그리기
        zoomG
          .insert('g', '.region-outline') // 아웃라인 아래에 삽입
          .selectAll<SVGPathElement, Feature<Geometry>>('path.province')
          .data(fc.features)
          .join('path')
          .attr('class', 'province')
          .attr('d', path as unknown as string)
          .attr('fill', 'white')
          .attr('stroke', '#C8C8C8')
          .attr('stroke-width', 0.8)
          .attr('stroke-linejoin', 'round');

        // ── 사전 계산 ────────────────────────────────────────────────────────
        const topoObj = topo.objects[TOPO_OBJECT_KEY] as TopoGeomCollection;

        // 1) 권역별 merged outline path 문자열
        MAP_REGIONS.forEach((region, idx) => {
          if (region.provinces === null) return;
          const selectedGeoms = topoObj.geometries.filter((g) => {
            const name = (g.properties as Record<string, string>)?.name ?? '';
            return isProvinceInRegion(name, region.provinces!);
          }) as Array<TopoPolygon | TopoMultiPolygon>;
          const merged = topojson.merge(topo, selectedGeoms);
          mergedPathsRef.current.set(idx, path(merged as Geometry) ?? '');
        });

        // 2) 각 시도 centroid(바운딩박스 중심) + projected bounding area
        // path.centroid()는 오목 도형(경기도 등)에서 실제 영역 밖에 위치할 수 있으므로
        // bounding box 중심점을 사용해 안정적인 지시선 끝점을 확보한다.
        fc.features.forEach((f) => {
          const name = getProvinceName(f);
          const b = path.bounds(f);
          const cx = (b[0][0] + b[1][0]) / 2;
          const cy = (b[0][1] + b[1][1]) / 2;
          centroidsRef.current.set(name, [cx, cy]);
          projAreasRef.current.set(name, (b[1][0] - b[0][0]) * (b[1][1] - b[0][1]));
        });

        setReady(true);
      });
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // ── 권역 업데이트 ────────────────────────────────────────────────────────────
  useEffect(() => {
    let labelTimer: ReturnType<typeof setTimeout> | null = null;

    const geo = geoRef.current;
    const path = pathRef.current;
    const zoomG = zoomGRef.current;
    const labelsG = labelsGRef.current;
    const outlineEl = outlineElRef.current;
    const container = containerRef.current;

    if (ready && geo && path && zoomG && labelsG && outlineEl && container) {
      const { width, height } = container.getBoundingClientRect();
      const w = width || 320;
      const h = height || 280;
      const region = MAP_REGIONS[regionIndex];

      const targetFeatures =
        region.provinces === null
          ? geo.features
          : geo.features.filter((f) => isProvinceInRegion(getProvinceName(f), region.provinces!));

      // 1. 줌 변환 계산
      const collection: FeatureCollection<Geometry> = { type: 'FeatureCollection', features: targetFeatures };
      const bounds = path.bounds(collection as Parameters<typeof path.bounds>[0]);
      const bdx = bounds[1][0] - bounds[0][0];
      const bdy = bounds[1][1] - bounds[0][1];
      const cx = (bounds[0][0] + bounds[1][0]) / 2;
      const cy = (bounds[0][1] + bounds[1][1]) / 2;
      const padding = region.provinces === null ? 0.85 : 0.7;
      const scale = Math.min((w / bdx) * padding, (h / bdy) * padding);
      const tx = w / 2 - scale * cx;
      const ty = h / 2 - scale * cy;

      // 2. 줌 애니메이션
      d3.select(zoomG)
        .transition()
        .duration(TRANSITION_DURATION)
        .ease(d3.easeQuintInOut)
        .attr('transform', `translate(${tx},${ty}) scale(${scale})`);

      // 3. 시도 스타일 업데이트
      const inRegion = (f: Feature<Geometry>) =>
        region.provinces !== null && isProvinceInRegion(getProvinceName(f), region.provinces);

      d3.select(zoomG)
        .selectAll<SVGPathElement, Feature<Geometry>>('path.province')
        .transition()
        .duration(TRANSITION_DURATION)
        .ease(d3.easeQuintInOut)
        .attr('fill', (f) => {
          const name = getProvinceName(f);
          const info = ELECTION_INFO[name];
          const poll = MOCK_POLL_DATA[name];
          if (!inRegion(f)) {
            if (region.provinces === null && info && poll) {
              const c1Leads = poll.c1Pct >= poll.c2Pct;
              return `${c1Leads ? info.c1.color : info.c2.color}26`;
            }
            return region.provinces === null ? '#F8F8F8' : 'white';
          }
          if (!info || !poll) return '#F0F4FF';
          const c1Leads = poll.c1Pct >= poll.c2Pct;
          const leadingColor = c1Leads ? info.c1.color : info.c2.color;
          return `${leadingColor}26`;
        })
        .attr('stroke', (f) => (inRegion(f) ? '#CCCCCC' : '#E8E8E8'))
        .attr('stroke-width', () => 0.6 / scale);

      // 4. 사전 계산된 아웃라인 적용 — path는 즉시 교체, opacity만 페이드인
      const outlinePath =
        region.provinces !== null
          ? mergedPathsRef.current.get(regionIndex) ?? ''
          : MAP_REGIONS.map((_, idx) => mergedPathsRef.current.get(idx) ?? '')
              .filter((p) => p)
              .join(' ');
      d3.select(outlineEl)
        .attr('d', outlinePath)
        .attr('stroke-width', region.provinces !== null ? 1.8 / scale : 1.0 / scale)
        .attr('opacity', 0)
        .transition()
        .duration(TRANSITION_DURATION)
        .ease(d3.easeQuintInOut)
        .attr('opacity', 1);

      // 5. 레이블: transition 완료 후 화면 좌표로 배치
      d3.select(labelsG).selectAll('*').remove();

      if (region.provinces !== null) {
        labelTimer = setTimeout(() => {
          d3.select(labelsG).selectAll('*').remove();

          // 사이드바에서 렌더링하므로 SVG 레이블 대신 centroid 위치만 콜백으로 전달
          const centroidsOut: CentroidInfo[] = [];
          targetFeatures.forEach((f) => {
            const name = getProvinceName(f);
            const centroid = centroidsRef.current.get(name);
            if (!centroid) return;
            const screenCx = tx + scale * centroid[0];
            const screenCy = ty + scale * centroid[1];
            centroidsOut.push({ provinceName: name, x: screenCx, y: screenCy });
          });
          onCentroidsReady?.(centroidsOut);
          onRegionCentroidsReady?.([]); // 권역 바로가기 숨김
        }, TRANSITION_DURATION + 50);
      } else {
        // 전체 보기: 시도 지시선 초기화 후 권역 중심 계산
        onCentroidsReady?.([]);
        labelTimer = setTimeout(() => {
          // 각 권역의 중심 = 소속 시도 바운딩박스 중심의 면적 가중 평균
          // 당선 정보 = 권역 내 국힘/민주 평균 득표율 비교
          const regionCentroidsOut: RegionCentroidInfo[] = [];
          MAP_REGIONS.forEach((r, idx) => {
            if (r.provinces === null) return;
            let totalArea = 0;
            let wcx = 0;
            let wcy = 0;
            let gukHimSum = 0;
            let minJuSum = 0;
            let pollCount = 0;
            const seen = new Set<string>();
            geo.features.forEach((f) => {
              const name = getProvinceName(f);
              if (!isProvinceInRegion(name, r.provinces!)) return;
              const area = projAreasRef.current.get(name) ?? 0;
              const c = centroidsRef.current.get(name);
              if (!c) return;
              wcx += area * c[0];
              wcy += area * c[1];
              totalArea += area;
              if (!seen.has(name)) {
                seen.add(name);
                const info = ELECTION_INFO[name];
                const poll = MOCK_POLL_DATA[name];
                if (info && poll) {
                  gukHimSum += info.c1.party === '국힘' ? poll.c1Pct : poll.c2Pct;
                  minJuSum += info.c1.party === '민주' ? poll.c1Pct : poll.c2Pct;
                  pollCount += 1;
                }
              }
            });
            if (totalArea > 0) {
              const gukHimAvg = pollCount > 0 ? gukHimSum / pollCount : 0;
              const minJuAvg = pollCount > 0 ? minJuSum / pollCount : 0;
              const leadingParty = gukHimAvg >= minJuAvg ? '국힘' : '민주';
              const leadingColor = gukHimAvg >= minJuAvg ? '#e61e2b' : '#152484';
              const leadingPct = Math.max(gukHimAvg, minJuAvg);
              regionCentroidsOut.push({
                regionIndex: idx,
                label: r.label,
                x: tx + scale * (wcx / totalArea),
                y: ty + scale * (wcy / totalArea),
                leadingParty,
                leadingColor,
                leadingPct,
              });
            }
          });
          onRegionCentroidsReady?.(regionCentroidsOut);
        }, TRANSITION_DURATION + 50);
      }
    }

    return () => {
      if (labelTimer !== null) clearTimeout(labelTimer);
    };
  }, [ready, regionIndex]);

  // ── 스와이프 제스처 ──────────────────────────────────────────────────────────
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
      const delta = e.changedTouches[0].clientX - touchStartX.current;
      touchStartX.current = null;
      if (delta < -SWIPE_THRESHOLD) goNext();
      else if (delta > SWIPE_THRESHOLD) goPrev();
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
      const delta = e.clientX - pointerStartX.current;
      pointerStartX.current = null;
      if (delta < -SWIPE_THRESHOLD) goNext();
      else if (delta > SWIPE_THRESHOLD) goPrev();
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
