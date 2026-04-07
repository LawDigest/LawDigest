'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import * as topojson from 'topojson-client';
import type { FeatureCollection, Feature, Geometry, Position } from 'geojson';
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

/** 작은 외딴 섬 제외 — MultiPolygon을 개별 폴리곤으로 분해 후 최대 면적 대비 2% 미만 폴리곤을 제외하고 경계 상자를 반환 */
function getBoundsMainland(features: Feature<Geometry>[], path: d3.GeoPath): [[number, number], [number, number]] {
  const polys: { b: [[number, number], [number, number]]; area: number }[] = [];

  const processRings = (coords: Position[][]) => {
    const poly: Feature<Geometry> = {
      type: 'Feature',
      properties: null,
      geometry: { type: 'Polygon', coordinates: coords },
    };
    const b = path.bounds(poly as Parameters<typeof path.bounds>[0]);
    const area = (b[1][0] - b[0][0]) * (b[1][1] - b[0][1]);
    if (area > 0) polys.push({ b, area });
  };

  features.forEach((f) => {
    const g = f.geometry;
    if (g.type === 'Polygon') {
      processRings(g.coordinates);
    } else if (g.type === 'MultiPolygon') {
      g.coordinates.forEach(processRings);
    }
  });

  if (polys.length === 0) {
    const fc: FeatureCollection<Geometry> = { type: 'FeatureCollection', features };
    return path.bounds(fc as Parameters<typeof path.bounds>[0]) as [[number, number], [number, number]];
  }

  const maxArea = Math.max(...polys.map((p) => p.area));
  const main = polys.filter((p) => p.area >= maxArea * 0.02);
  const use = main.length > 0 ? main : polys;

  return [
    [Math.min(...use.map((p) => p.b[0][0])), Math.min(...use.map((p) => p.b[0][1]))],
    [Math.max(...use.map((p) => p.b[1][0])), Math.max(...use.map((p) => p.b[1][1]))],
  ];
}

// ─── 컴포넌트 ─────────────────────────────────────────────────────────────────

interface KoreaMapProps {
  regionIndex: number;
  onRegionChange: (index: number) => void;
  onCentroidsReady?: (centroids: CentroidInfo[]) => void;
  onRegionCentroidsReady?: (centroids: RegionCentroidInfo[]) => void;
  mapHeight?: number;
}

export default function KoreaMap({
  regionIndex,
  onRegionChange,
  onCentroidsReady,
  onRegionCentroidsReady,
  mapHeight = 280,
}: KoreaMapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const svgRef = useRef<SVGSVGElement>(null);
  const zoomGRef = useRef<SVGGElement | null>(null);
  const outlineElRef = useRef<SVGPathElement | null>(null);
  const labelsGRef = useRef<SVGGElement | null>(null);
  const pathRef = useRef<d3.GeoPath | null>(null);
  const projectionRef = useRef<d3.GeoProjection | null>(null);
  const geoRef = useRef<FeatureCollection<Geometry> | null>(null);
  /** 각 권역 index → 사전 계산된 SVG path 문자열 */
  const mergedPathsRef = useRef<Map<number, string>>(new Map());
  /** 시도명 → projection 좌표 centroid */
  const centroidsRef = useRef<Map<string, [number, number]>>(new Map());
  /** 시도명 → projection 좌표 기준 bounding box 면적 */
  const projAreasRef = useRef<Map<string, number>>(new Map());
  const [ready, setReady] = useState(false);

  // 클릭 핸들러에서 최신 값에 접근하기 위한 refs
  const regionIndexRef = useRef(regionIndex);
  const onRegionChangeRef = useRef(onRegionChange);
  useEffect(() => {
    regionIndexRef.current = regionIndex;
  }, [regionIndex]);
  useEffect(() => {
    onRegionChangeRef.current = onRegionChange;
  }, [onRegionChange]);

  // ── 초기화 (1회) ───────────────────────────────────────────────────────────
  useEffect(() => {
    const svg = svgRef.current;
    const container = containerRef.current;
    if (!svg || !container) return;

    const { width } = container.getBoundingClientRect();
    const w = width || 320;
    const h = mapHeight;

    d3.select(svg).selectAll('*').remove();

    const projection = d3
      .geoMercator()
      .center([127.8, 36.3])
      .scale(w * 5.0)
      .translate([w / 2, h / 2]);
    const path = d3.geoPath().projection(projection);
    pathRef.current = path;
    projectionRef.current = projection;

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
          .attr('stroke-linejoin', 'round')
          .on('click', (_event, f) => {
            // 전국 뷰에서만: 클릭한 시도가 속한 권역으로 이동
            if (regionIndexRef.current !== 0) return;
            const name = getProvinceName(f);
            const idx = MAP_REGIONS.findIndex(
              (r, i) => i !== 0 && r.provinces !== null && isProvinceInRegion(name, r.provinces),
            );
            if (idx !== -1) onRegionChangeRef.current(idx);
          });

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
      const { width } = container.getBoundingClientRect();
      const w = width || 320;
      const h = mapHeight;
      const region = MAP_REGIONS[regionIndex];

      const targetFeatures =
        region.provinces === null
          ? geo.features
          : geo.features.filter((f) => isProvinceInRegion(getProvinceName(f), region.provinces!));

      // 1. 줌 변환 계산 (원거리 섬 제외)
      const bounds = getBoundsMainland(targetFeatures, path);
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
        .ease(d3.easeCubicInOut)
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
        .attr('stroke', (f) => {
          if (region.provinces === null) return 'none'; // 전국 뷰: 시도 경계 숨김
          return inRegion(f) ? '#999999' : '#E8E8E8';
        })
        .attr('stroke-width', (f) => (inRegion(f) ? 1.2 / scale : 0.6 / scale));

      // 커서 스타일: 전국 뷰에서 pointer, 권역 뷰에서 default
      d3.select(zoomG)
        .selectAll<SVGPathElement, Feature<Geometry>>('path.province')
        .style('cursor', region.provinces === null ? 'pointer' : 'default');

      // 4. 사전 계산된 아웃라인 적용 — path는 즉시 교체, opacity만 페이드인
      const outlinePath =
        region.provinces !== null
          ? mergedPathsRef.current.get(regionIndex) ?? ''
          : MAP_REGIONS.map((_, idx) => mergedPathsRef.current.get(idx) ?? '')
              .filter((p) => p)
              .join(' ');
      d3.select(outlineEl)
        .attr('d', outlinePath)
        .attr('stroke-width', region.provinces !== null ? 1.8 / scale : 0.8 / scale)
        .attr('opacity', 0)
        .transition()
        .duration(TRANSITION_DURATION)
        .ease(d3.easeCubicInOut)
        .attr('opacity', 1);

      // 5. 레이블: transition 완료 후 화면 좌표로 배치
      d3.select(labelsG).selectAll('*').remove();

      if (region.provinces !== null) {
        labelTimer = setTimeout(() => {
          d3.select(labelsG).selectAll('*').remove();

          // 사이드바에서 렌더링하므로 SVG 레이블 대신 centroid 위치만 콜백으로 전달
          // 섬이 많거나 오목한 지역은 bounding box 중심이 바다/외부로 치우치므로 내륙 위경도 사용
          const CENTROID_LNGLAT: Record<string, [number, number]> = {
            서울특별시: [126.978, 37.566],
            인천광역시: [126.72, 37.46], // 서해 도서 제외, 부평/남동 일대
            경기도: [127.15, 37.3],
            부산광역시: [129.05, 35.15],
            대구광역시: [128.6, 35.87],
            광주광역시: [126.85, 35.16],
            대전광역시: [127.38, 36.35],
            울산광역시: [129.31, 35.54],
            세종특별자치시: [127.29, 36.48],
            강원특별자치도: [128.2, 37.6], // 동해안 섬 제외, 내륙 중심
            강원도: [128.2, 37.6],
            충청북도: [127.73, 36.8],
            충청남도: [126.8, 36.5], // 서해 도서 제외
            전북특별자치도: [127.1, 35.7],
            전라북도: [127.1, 35.7],
            전라남도: [127.1, 34.9], // 남해 도서 제외
            경상북도: [128.8, 36.4],
            경상남도: [128.25, 35.4], // 남해 도서 제외
            제주특별자치도: [126.55, 33.4],
          };
          const proj = projectionRef.current;
          const centroidsOut: CentroidInfo[] = [];
          targetFeatures.forEach((f) => {
            const name = getProvinceName(f);
            const overrideLngLat = CENTROID_LNGLAT[name];
            let screenCx: number;
            let screenCy: number;
            if (overrideLngLat && proj) {
              const projected = proj(overrideLngLat);
              if (projected) {
                screenCx = tx + scale * projected[0];
                screenCy = ty + scale * projected[1];
              } else {
                const centroid = centroidsRef.current.get(name);
                if (!centroid) return;
                screenCx = tx + scale * centroid[0];
                screenCy = ty + scale * centroid[1];
              }
            } else {
              const centroid = centroidsRef.current.get(name);
              if (!centroid) return;
              screenCx = tx + scale * centroid[0];
              screenCy = ty + scale * centroid[1];
            }
            centroidsOut.push({ provinceName: name, x: screenCx, y: screenCy });
          });
          onCentroidsReady?.(centroidsOut);

          // 각 시도 이름을 내륙 centroid 위치에 SVG 텍스트로 표시
          centroidsOut.forEach(({ provinceName: name, x: screenCx, y: screenCy }) => {
            // 짧은 표시명 (광역시·도 → 시·도 약칭)
            const SHORT_NAME: Record<string, string> = {
              서울특별시: '서울',
              인천광역시: '인천',
              경기도: '경기',
              부산광역시: '부산',
              대구광역시: '대구',
              광주광역시: '광주',
              대전광역시: '대전',
              울산광역시: '울산',
              세종특별자치시: '세종',
              강원특별자치도: '강원',
              강원도: '강원',
              충청북도: '충북',
              충청남도: '충남',
              전북특별자치도: '전북',
              전라북도: '전북',
              전라남도: '전남',
              경상북도: '경북',
              경상남도: '경남',
              제주특별자치도: '제주',
            };
            const label = SHORT_NAME[name] ?? name;
            d3.select(labelsG)
              .append('text')
              .attr('x', screenCx)
              .attr('y', screenCy)
              .attr('text-anchor', 'middle')
              .attr('dominant-baseline', 'middle')
              .attr('font-size', 11)
              .attr('font-weight', '600')
              .attr('fill', '#374151')
              .attr('opacity', 0)
              .attr('pointer-events', 'none')
              .text(label)
              .transition()
              .duration(300)
              .attr('opacity', 0.7);
          });

          onRegionCentroidsReady?.([]); // 권역 바로가기 숨김
        }, TRANSITION_DURATION + 50);
      } else {
        // 전체 보기: 시도 지시선 초기화 후 권역 중심 계산
        onCentroidsReady?.([]);
        labelTimer = setTimeout(() => {
          // 각 권역의 중심 = 소속 시도 바운딩박스 중심의 면적 가중 평균
          // 당선 정보 = 권역 내 국힘/민주 평균 득표율 비교
          // 전국 뷰 권역 centroid: 각 시도의 내륙 위경도 기준 면적 가중 평균
          const INLAND_LNGLAT: Record<string, [number, number]> = {
            서울특별시: [126.978, 37.566],
            인천광역시: [126.72, 37.46],
            경기도: [127.15, 37.3],
            부산광역시: [129.05, 35.15],
            대구광역시: [128.6, 35.87],
            광주광역시: [126.85, 35.16],
            대전광역시: [127.38, 36.35],
            울산광역시: [129.31, 35.2],
            세종특별자치시: [127.29, 36.48],
            강원특별자치도: [128.2, 37.6],
            강원도: [128.2, 37.6],
            충청북도: [127.73, 36.8],
            충청남도: [126.8, 36.5],
            전북특별자치도: [127.1, 35.7],
            전라북도: [127.1, 35.7],
            전라남도: [127.1, 34.9],
            경상북도: [128.8, 36.4],
            경상남도: [128.25, 35.4],
            제주특별자치도: [126.55, 33.4],
          };
          const proj = projectionRef.current;
          const regionCentroidsOut: RegionCentroidInfo[] = [];
          MAP_REGIONS.forEach((r, idx) => {
            if (r.provinces === null) return;
            let totalWeight = 0;
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
              // 내륙 위경도가 있으면 그 좌표를 사용, 없으면 bounding box 중심
              const inlandLngLat = INLAND_LNGLAT[name];
              let projectedCx: number;
              let projectedCy: number;
              if (inlandLngLat && proj) {
                const projected = proj(inlandLngLat);
                if (projected) {
                  [projectedCx, projectedCy] = projected;
                } else {
                  const c = centroidsRef.current.get(name);
                  if (!c) return;
                  [projectedCx, projectedCy] = c;
                }
              } else {
                const c = centroidsRef.current.get(name);
                if (!c) return;
                [projectedCx, projectedCy] = c;
              }
              wcx += area * projectedCx;
              wcy += area * projectedCy;
              totalWeight += area;
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
            if (totalWeight > 0) {
              const gukHimAvg = pollCount > 0 ? gukHimSum / pollCount : 0;
              const minJuAvg = pollCount > 0 ? minJuSum / pollCount : 0;
              const leadingParty = gukHimAvg >= minJuAvg ? '국힘' : '민주';
              const leadingColor = gukHimAvg >= minJuAvg ? '#e61e2b' : '#152484';
              const leadingPct = Math.max(gukHimAvg, minJuAvg);
              regionCentroidsOut.push({
                regionIndex: idx,
                label: r.label,
                x: tx + scale * (wcx / totalWeight),
                y: ty + scale * (wcy / totalWeight),
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
      style={{ touchAction: 'pan-y', WebkitTapHighlightColor: 'transparent' }}
      onTouchStart={handleTouchStart}
      onTouchEnd={handleTouchEnd}
      onPointerDown={handlePointerDown}
      onPointerUp={handlePointerUp}>
      <svg
        ref={svgRef}
        className="w-full"
        style={{ height: mapHeight }}
        viewBox={`0 0 ${containerRef.current?.clientWidth || 320} ${mapHeight}`}
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
