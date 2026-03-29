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

// ─── 상수 ─────────────────────────────────────────────────────────────────────

const TOPO_OBJECT_KEY = 'skorea_provinces_geo';
const TRANSITION_DURATION = 500;
const SWIPE_THRESHOLD = 40;
/** 이 값(screen px²) 미만이면 지시선 레이블을 사용 */
const SMALL_AREA_THRESHOLD = 2800;

// ─── 선거 데이터 (제9회 전국동시지방선거 mock – 8회 결과 기준) ─────────────────

interface CandidateInfo {
  name: string;
  party: string;
  color: string;
}

interface ProvinceElectionInfo {
  title: string;
  c1: CandidateInfo;
  c2: CandidateInfo;
}

const ELECTION_INFO: Record<string, ProvinceElectionInfo> = {
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

const PROVINCE_SHORT_NAME: Record<string, string> = {
  서울특별시: '서울',
  부산광역시: '부산',
  대구광역시: '대구',
  인천광역시: '인천',
  광주광역시: '광주',
  대전광역시: '대전',
  울산광역시: '울산',
  세종특별자치시: '세종',
  경기도: '경기',
  강원도: '강원',
  강원특별자치도: '강원',
  충청북도: '충북',
  충청남도: '충남',
  전라북도: '전북',
  전북특별자치도: '전북',
  전라남도: '전남',
  경상북도: '경북',
  경상남도: '경남',
  제주특별자치도: '제주',
};

/** 소규모 시도 지시선 오프셋 [dx, dy] (screen px) */
const LEADER_OFFSET: Record<string, [number, number]> = {
  서울특별시: [0, -38],
  인천광역시: [-52, 8],
  세종특별자치시: [30, -22],
  대전광역시: [-52, 0],
  광주광역시: [-52, 0],
  대구광역시: [40, -28],
  부산광역시: [40, 26],
  울산광역시: [50, -5],
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
}

export default function KoreaMap({ regionIndex, onRegionChange }: KoreaMapProps) {
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

        // 2) 각 시도 centroid + projected bounding area
        fc.features.forEach((f) => {
          const name = getProvinceName(f);
          centroidsRef.current.set(name, path.centroid(f) as [number, number]);
          const b = path.bounds(f);
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
        .ease(d3.easeCubicInOut)
        .attr('transform', `translate(${tx},${ty}) scale(${scale})`);

      // 3. 시도 스타일 업데이트
      const inRegion = (f: Feature<Geometry>) =>
        region.provinces !== null && isProvinceInRegion(getProvinceName(f), region.provinces);

      d3.select(zoomG)
        .selectAll<SVGPathElement, Feature<Geometry>>('path.province')
        .transition()
        .duration(TRANSITION_DURATION)
        .attr('fill', (f) => (inRegion(f) ? '#F0F4FF' : 'white'))
        .attr('stroke', (f) => (inRegion(f) ? '#CCCCCC' : '#E8E8E8'))
        .attr('stroke-width', () => 0.6 / scale);

      // 4. 사전 계산된 아웃라인 적용 (DOM remove/add 없이 d 속성만 교체)
      const outlinePath = region.provinces !== null ? mergedPathsRef.current.get(regionIndex) ?? '' : '';
      d3.select(outlineEl)
        .attr('d', outlinePath)
        .attr('stroke-width', region.provinces !== null ? 1.8 / scale : 0);

      // 5. 레이블: transition 완료 후 화면 좌표로 배치
      d3.select(labelsG).selectAll('*').remove();

      if (region.provinces !== null) {
        labelTimer = setTimeout(() => {
          d3.select(labelsG).selectAll('*').remove();

          targetFeatures.forEach((f) => {
            const name = getProvinceName(f);
            const info = ELECTION_INFO[name];
            const shortName = PROVINCE_SHORT_NAME[name] ?? name;
            if (!info) return;

            // 사전 계산된 centroid / 면적 사용
            const centroid = centroidsRef.current.get(name);
            if (!centroid) return;
            const screenCx = tx + scale * centroid[0];
            const screenCy = ty + scale * centroid[1];

            const projArea = projAreasRef.current.get(name) ?? 0;
            const needsLeader = projArea * scale * scale < SMALL_AREA_THRESHOLD;
            const offset = needsLeader ? LEADER_OFFSET[name] ?? [0, 0] : [0, 0];
            const textX = screenCx + offset[0];
            const textY = screenCy + offset[1];

            const lg = d3.select(labelsG).append('g').attr('class', 'label-group');

            // 지시선
            if (needsLeader && (offset[0] !== 0 || offset[1] !== 0)) {
              lg.append('line')
                .attr('x1', screenCx)
                .attr('y1', screenCy)
                .attr('x2', textX)
                .attr('y2', textY)
                .attr('stroke', '#9CA3AF')
                .attr('stroke-width', 0.8)
                .attr('stroke-dasharray', '2,1.5');

              lg.append('circle').attr('cx', screenCx).attr('cy', screenCy).attr('r', 2).attr('fill', '#9CA3AF');
            }

            const textG = lg.append('g').attr('transform', `translate(${textX},${textY})`);

            const addText = (textDy: number, fontSize: number, fontWeight: string, fill: string, content: string) => {
              textG
                .append('text')
                .attr('dy', textDy)
                .attr('font-size', fontSize)
                .attr('font-weight', fontWeight)
                .attr('fill', fill)
                .attr('text-anchor', 'middle')
                .attr('stroke', 'rgba(255,255,255,0.9)')
                .attr('stroke-width', 3)
                .attr('paint-order', 'stroke')
                .attr('stroke-linejoin', 'round')
                .text(content);
            };

            addText(0, 10, '700', '#1A202C', shortName);
            addText(14, 8.5, '400', info.c1.color, `${info.c1.name}(${info.c1.party})`);
            addText(26, 8.5, '400', info.c2.color, `${info.c2.name}(${info.c2.party})`);
          });
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
