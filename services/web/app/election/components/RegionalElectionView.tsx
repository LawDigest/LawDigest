'use client';

import { useEffect, useMemo, useState } from 'react';
import { Button, Card, CardBody, CardHeader, Chip, Spinner } from '@nextui-org/react';
import { ElectionCandidateId, ElectionId, ElectionRegionCode, ElectionRegionType, ElectionViewMode } from '@/types';
import { useGetElectionCandidates, useGetElectionOverview, useGetElectionRegionPanel } from '../apis/queries';
import { getRegionTypeLabel, getTemplateLabel } from '../utils/electionLabels';
import ElectionDetailPanel from './ElectionDetailPanel';

interface RegionalElectionViewProps {
  electionId: ElectionId;
  regionCode: ElectionRegionCode;
  regionType: ElectionRegionType;
  regionName: string;
}

interface MapNode {
  regionCode: ElectionRegionCode;
  regionName: string;
  regionType: ElectionRegionType;
  resultLabel: string;
  resultValue: string;
  children?: MapNode[];
}

interface MapFamilyDefinition {
  root: MapNode;
  nextDepthLabel: string;
  terminalDepthLabel: string;
}

interface CandidateViewModel {
  candidate_id: ElectionCandidateId;
  candidate_name: string;
  party_name: string;
  candidate_image_url: string;
  fallbackSummary?: string;
  fallbackItems?: string[];
}

type BreadcrumbNode = {
  regionCode: ElectionRegionCode;
  regionName: string;
  regionType: ElectionRegionType;
};

const ACTUAL_MAP_VIEW_MODE: ElectionViewMode = 'RESULT';
const CARTOGRAM_VIEW_MODE = 'HEX' as ElectionViewMode;

const ASSEMBLY_MAP_TREE: MapFamilyDefinition = {
  nextDepthLabel: '시/도',
  terminalDepthLabel: '선거구',
  root: {
    regionCode: 'national',
    regionName: '전국',
    regionType: 'NATIONAL',
    resultLabel: '의석 흐름',
    resultValue: '수도권 경합, 부산·경남 혼전',
    children: [
      {
        regionCode: 'seoul',
        regionName: '서울특별시',
        regionType: 'PROVINCE',
        resultLabel: '격전 지역',
        resultValue: '종로·용산·마포',
        children: [
          {
            regionCode: 'seoul-jongno',
            regionName: '종로구',
            regionType: 'DISTRICT',
            resultLabel: '지난 결과',
            resultValue: '민주 48.1% / 국민의힘 45.6%',
          },
          {
            regionCode: 'seoul-yongsan',
            regionName: '용산구',
            regionType: 'DISTRICT',
            resultLabel: '지난 결과',
            resultValue: '국민의힘 51.2% / 민주 43.7%',
          },
          {
            regionCode: 'seoul-mapo-gap',
            regionName: '마포갑',
            regionType: 'DISTRICT',
            resultLabel: '지난 결과',
            resultValue: '민주 49.8% / 국민의힘 44.9%',
          },
        ],
      },
      {
        regionCode: 'busan',
        regionName: '부산광역시',
        regionType: 'PROVINCE',
        resultLabel: '주요 관전',
        resultValue: '중·영도 / 사상 / 해운대',
        children: [
          {
            regionCode: 'busan-sasang',
            regionName: '사상구',
            regionType: 'DISTRICT',
            resultLabel: '지난 결과',
            resultValue: '국민의힘 52.4% / 민주 41.8%',
          },
          {
            regionCode: 'busan-haeundae',
            regionName: '해운대구갑',
            regionType: 'DISTRICT',
            resultLabel: '지난 결과',
            resultValue: '국민의힘 55.1% / 민주 39.4%',
          },
        ],
      },
      {
        regionCode: 'gyeonggi',
        regionName: '경기도',
        regionType: 'PROVINCE',
        resultLabel: '수도권 확장',
        resultValue: '수원·성남·고양 중심',
        children: [
          {
            regionCode: 'gyeonggi-seongnam',
            regionName: '성남시분당구갑',
            regionType: 'DISTRICT',
            resultLabel: '지난 결과',
            resultValue: '국민의힘 50.7% / 민주 44.5%',
          },
          {
            regionCode: 'gyeonggi-suwon',
            regionName: '수원시갑',
            regionType: 'DISTRICT',
            resultLabel: '지난 결과',
            resultValue: '민주 47.3% / 국민의힘 46.2%',
          },
        ],
      },
    ],
  },
};

const LOCAL_MAP_TREE: MapFamilyDefinition = {
  nextDepthLabel: '시/도',
  terminalDepthLabel: '시군구',
  root: {
    regionCode: 'national',
    regionName: '전국',
    regionType: 'NATIONAL',
    resultLabel: '판세 요약',
    resultValue: '광역·기초단체장 혼합 경쟁 구도',
    children: [
      {
        regionCode: 'seoul',
        regionName: '서울특별시',
        regionType: 'PROVINCE',
        resultLabel: '기초단체장 관전',
        resultValue: '종로·중구·마포',
        children: [
          {
            regionCode: 'seoul-jongno',
            regionName: '종로구',
            regionType: 'COUNTY',
            resultLabel: '지난 결과',
            resultValue: '구청장 민주 50.4% / 국민의힘 45.8%',
          },
          {
            regionCode: 'seoul-mapo',
            regionName: '마포구',
            regionType: 'COUNTY',
            resultLabel: '지난 결과',
            resultValue: '구청장 국민의힘 49.9% / 민주 46.1%',
          },
        ],
      },
      {
        regionCode: 'gyeonggi',
        regionName: '경기도',
        regionType: 'PROVINCE',
        resultLabel: '광역단체장 관전',
        resultValue: '성남·수원·고양',
        children: [
          {
            regionCode: 'gyeonggi-seongnam',
            regionName: '성남시',
            regionType: 'COUNTY',
            resultLabel: '지난 결과',
            resultValue: '시장 민주 51.0% / 국민의힘 43.6%',
          },
          {
            regionCode: 'gyeonggi-suwon',
            regionName: '수원시',
            regionType: 'COUNTY',
            resultLabel: '지난 결과',
            resultValue: '시장 민주 49.2% / 국민의힘 45.1%',
          },
        ],
      },
      {
        regionCode: 'busan',
        regionName: '부산광역시',
        regionType: 'PROVINCE',
        resultLabel: '교육감·기초단체장',
        resultValue: '사상·해운대·수영',
        children: [
          {
            regionCode: 'busan-sasang',
            regionName: '사상구',
            regionType: 'COUNTY',
            resultLabel: '지난 결과',
            resultValue: '구청장 국민의힘 53.0% / 민주 40.2%',
          },
          {
            regionCode: 'busan-haeundae',
            regionName: '해운대구',
            regionType: 'COUNTY',
            resultLabel: '지난 결과',
            resultValue: '구청장 국민의힘 56.4% / 민주 36.7%',
          },
        ],
      },
    ],
  },
};

const isAssemblyElection = (electionId: ElectionId) => electionId.startsWith('assembly');

const getMapDefinition = (electionId: ElectionId) =>
  isAssemblyElection(electionId) ? ASSEMBLY_MAP_TREE : LOCAL_MAP_TREE;

const getInitialPath = (definition: MapFamilyDefinition): BreadcrumbNode[] => [
  {
    regionCode: definition.root.regionCode,
    regionName: definition.root.regionName,
    regionType: definition.root.regionType,
  },
];

const findNodeByCode = (node: MapNode, regionCode: ElectionRegionCode): MapNode | null => {
  if (node.regionCode === regionCode) {
    return node;
  }

  return (node.children ?? []).reduce<MapNode | null>((matchedNode, childNode) => {
    if (matchedNode) {
      return matchedNode;
    }

    return findNodeByCode(childNode, regionCode);
  }, null);
};

const getCurrentNode = (definition: MapFamilyDefinition, path: BreadcrumbNode[]) => {
  const currentCode = path[path.length - 1]?.regionCode ?? definition.root.regionCode;

  return findNodeByCode(definition.root, currentCode) ?? definition.root;
};

const getRegionContextLabel = (regionType: ElectionRegionType) => {
  if (regionType === 'DISTRICT') {
    return '선거구';
  }

  if (regionType === 'COUNTY') {
    return '시군구';
  }

  if (regionType === 'PROVINCE') {
    return '시/도';
  }

  return '전국';
};

const buildPlaceholderCandidates = (activeRegion: BreadcrumbNode): CandidateViewModel[] => [
  {
    candidate_id: `mock-${activeRegion.regionCode}-1`,
    candidate_name: `${activeRegion.regionName} 예시 후보 A`,
    party_name: '예시 정당 A',
    candidate_image_url: '',
    fallbackSummary: `${activeRegion.regionName} 기준 주요 현안을 설명하는 예시 공약 요약입니다.`,
    fallbackItems: [
      `${activeRegion.regionName} 생활 인프라 개선`,
      `${activeRegion.regionName} 교통·안전 예산 우선 배분`,
    ],
  },
  {
    candidate_id: `mock-${activeRegion.regionCode}-2`,
    candidate_name: `${activeRegion.regionName} 예시 후보 B`,
    party_name: '예시 정당 B',
    candidate_image_url: '',
    fallbackSummary: `${activeRegion.regionName} 지역 현안을 다른 방향으로 풀어내는 예시 공약 요약입니다.`,
    fallbackItems: [`${activeRegion.regionName} 청년·주거 지원`, `${activeRegion.regionName} 공공서비스 접근성 강화`],
  },
];

export default function RegionalElectionView({
  electionId,
  regionCode,
  regionType,
  regionName,
}: RegionalElectionViewProps) {
  const mapDefinition = useMemo(() => getMapDefinition(electionId), [electionId]);

  const [selectedCandidateId, setSelectedCandidateId] = useState<ElectionCandidateId | null>(null);
  const [viewMode, setViewMode] = useState<ElectionViewMode>(ACTUAL_MAP_VIEW_MODE);
  const [navigationPath, setNavigationPath] = useState<BreadcrumbNode[]>(() => getInitialPath(mapDefinition));

  useEffect(() => {
    setNavigationPath(getInitialPath(mapDefinition));
    setViewMode(ACTUAL_MAP_VIEW_MODE);
  }, [mapDefinition]);

  const currentNode = useMemo(() => getCurrentNode(mapDefinition, navigationPath), [mapDefinition, navigationPath]);
  const childNodes = currentNode.children ?? [];
  const reachedTerminalDepth = childNodes.length === 0;

  const activeRegion = useMemo<BreadcrumbNode>(
    () => ({
      regionCode: currentNode.regionCode,
      regionName: currentNode.regionName,
      regionType: currentNode.regionType,
    }),
    [currentNode],
  );

  const overviewQuery = useGetElectionOverview(electionId, activeRegion.regionType, activeRegion.regionCode);
  const panelQuery = useGetElectionRegionPanel(electionId, activeRegion.regionType, activeRegion.regionCode, null);
  const candidatesQuery = useGetElectionCandidates(electionId, activeRegion.regionCode, null);

  const overview = overviewQuery.data?.data;
  const panel = panelQuery.data?.data;
  const candidatesResponse = candidatesQuery.data?.data;
  const hasRegionMatchedCandidates =
    candidatesResponse?.region_code === activeRegion.regionCode && (candidatesResponse?.candidates?.length ?? 0) > 0;
  const candidates = useMemo<CandidateViewModel[]>(
    () =>
      hasRegionMatchedCandidates ? candidatesResponse?.candidates ?? [] : buildPlaceholderCandidates(activeRegion),
    [activeRegion, candidatesResponse?.candidates, hasRegionMatchedCandidates],
  );

  useEffect(() => {
    if (!candidates.length) {
      setSelectedCandidateId(null);
      return;
    }

    setSelectedCandidateId((current) => {
      if (current && candidates.some(({ candidate_id }) => candidate_id === current)) {
        return current;
      }

      return candidates[0].candidate_id;
    });
  }, [candidates]);

  const isLoading = overviewQuery.isLoading || panelQuery.isLoading || candidatesQuery.isLoading;

  const selectedCandidate = useMemo(
    () => candidates.find(({ candidate_id }) => candidate_id === selectedCandidateId) ?? null,
    [candidates, selectedCandidateId],
  );
  const panelTitle =
    panel?.region_code === activeRegion.regionCode
      ? panel?.result_card.title
      : `${activeRegion.regionName} 중심 결과 요약`;

  if (isLoading) {
    return (
      <Card className="border border-default-200 bg-transparent">
        <CardBody className="flex min-h-[320px] items-center justify-center">
          <Spinner color="default" label="지역 선거 정보를 불러오는 중입니다." />
        </CardBody>
      </Card>
    );
  }

  return (
    <section className="grid gap-6 xl:grid-cols-[minmax(0,1.45fr)_minmax(320px,0.85fr)]">
      <section className="grid gap-6">
        <Card className="border border-default-200 bg-transparent">
          <CardHeader className="flex flex-col items-start gap-3 p-6">
            <div className="flex flex-wrap items-center gap-2">
              <Chip variant="flat">{getRegionTypeLabel(activeRegion.regionType)}</Chip>
              <Chip variant="bordered">{activeRegion.regionCode}</Chip>
              {overview?.ui_template ? <Chip variant="bordered">{getTemplateLabel(overview.ui_template)}</Chip> : null}
            </div>
            <div className="space-y-1">
              <h2 className="text-2xl font-semibold">{activeRegion.regionName}</h2>
              <p className="text-sm leading-6 text-gray-500">
                {panelTitle ??
                  overview?.default_result_card.title ??
                  '지역 결과 카드 정보가 연결되면 여기에 요약이 표시됩니다.'}
              </p>
            </div>
          </CardHeader>
          <CardBody className="grid gap-4 p-6 pt-0 lg:grid-cols-[minmax(0,1.2fr)_minmax(280px,0.8fr)]">
            <div className="rounded-2xl border border-default-200 bg-default-50 p-4">
              <p className="text-xs font-medium uppercase tracking-[0.16em] text-gray-500">기본 결과 카드</p>
              <p className="mt-3 text-lg font-semibold">
                {overview?.default_result_card.title ?? '결과 카드 데이터 대기 중'}
              </p>
            </div>
            <div className="grid gap-3 rounded-2xl border border-default-200 p-4">
              <div className="flex items-center justify-between gap-3">
                <p className="text-xs font-medium uppercase tracking-[0.16em] text-gray-500">탐색 상태</p>
                <Chip size="sm" variant="flat">
                  {isAssemblyElection(electionId) ? '총선' : '지방선거'} depth
                </Chip>
              </div>
              <div className="grid gap-2 text-sm text-gray-600 sm:grid-cols-2">
                <div>
                  <p className="text-xs uppercase tracking-[0.16em] text-gray-400">현재 깊이</p>
                  <p className="mt-1 font-semibold text-black">{getRegionContextLabel(currentNode.regionType)}</p>
                </div>
                <div>
                  <p className="text-xs uppercase tracking-[0.16em] text-gray-400">다음 단계</p>
                  <p className="mt-1 font-semibold text-black">
                    {reachedTerminalDepth ? mapDefinition.terminalDepthLabel : mapDefinition.nextDepthLabel}
                  </p>
                </div>
              </div>
              <p className="text-sm leading-6 text-gray-500">
                현재 API가 완전히 연결되지 않아도 지도 탐색 상태와 화면 전환은 mock 데이터 기준으로 먼저 동작합니다.
              </p>
            </div>
          </CardBody>
        </Card>

        <Card className="border border-default-200 bg-transparent">
          <CardHeader className="flex flex-col gap-4 p-6">
            <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
              <div className="space-y-1">
                <h3 className="text-xl font-semibold">지도 탐색</h3>
                <p className="text-sm leading-6 text-gray-500">
                  {isAssemblyElection(electionId)
                    ? '전국 → 시/도 → 선거구 흐름으로 내려갑니다.'
                    : '전국 → 시/도 → 시군구 흐름으로 내려갑니다.'}
                </p>
              </div>
              <div className="inline-flex rounded-2xl border border-default-200 p-1">
                <Button
                  size="sm"
                  radius="lg"
                  variant={viewMode === ACTUAL_MAP_VIEW_MODE ? 'solid' : 'light'}
                  color={viewMode === ACTUAL_MAP_VIEW_MODE ? 'default' : undefined}
                  aria-pressed={viewMode === ACTUAL_MAP_VIEW_MODE}
                  onClick={() => setViewMode(ACTUAL_MAP_VIEW_MODE)}>
                  실제 지도
                </Button>
                <Button
                  size="sm"
                  radius="lg"
                  variant={viewMode === CARTOGRAM_VIEW_MODE ? 'solid' : 'light'}
                  color={viewMode === CARTOGRAM_VIEW_MODE ? 'default' : undefined}
                  aria-pressed={viewMode === CARTOGRAM_VIEW_MODE}
                  onClick={() => setViewMode(CARTOGRAM_VIEW_MODE)}>
                  육각형 카토그램
                </Button>
              </div>
            </div>

            <nav aria-label="지역 depth breadcrumb" className="flex flex-wrap items-center gap-2">
              {navigationPath.map((node, index) => {
                const isCurrent = index === navigationPath.length - 1;

                return (
                  <div key={node.regionCode} className="flex items-center gap-2">
                    <Button
                      size="sm"
                      variant={isCurrent ? 'solid' : 'bordered'}
                      color={isCurrent ? 'default' : undefined}
                      onClick={() => setNavigationPath((current) => current.slice(0, index + 1))}>
                      {node.regionName}
                    </Button>
                    {index < navigationPath.length - 1 ? <span className="text-xs text-gray-400">/</span> : null}
                  </div>
                );
              })}
            </nav>
          </CardHeader>

          <CardBody className="grid gap-4 p-6 pt-0">
            <section
              data-testid="regional-map-stage"
              className={`rounded-[28px] border p-4 sm:p-5 ${
                viewMode === ACTUAL_MAP_VIEW_MODE
                  ? 'border-default-200 bg-gradient-to-br from-white via-default-50 to-default-100'
                  : 'border-default-300 bg-[radial-gradient(circle_at_top,_rgba(0,0,0,0.06),_transparent_42%),linear-gradient(135deg,#f8fafc,#eef2f7)]'
              }`}>
              <div className="flex flex-col gap-3 border-b border-default-200 pb-4 sm:flex-row sm:items-start sm:justify-between">
                <div className="space-y-1">
                  <p className="text-xs font-medium uppercase tracking-[0.16em] text-gray-500">
                    {viewMode === ACTUAL_MAP_VIEW_MODE ? '실제 지도' : '육각형 카토그램'}
                  </p>
                  <h4 className="text-lg font-semibold">{currentNode.regionName}</h4>
                  <p className="text-sm leading-6 text-gray-500">
                    {currentNode.resultLabel} · {currentNode.resultValue}
                  </p>
                </div>
                <Chip variant="bordered">{getRegionTypeLabel(currentNode.regionType)}</Chip>
              </div>

              <div
                className={`mt-4 grid gap-3 ${
                  viewMode === ACTUAL_MAP_VIEW_MODE ? 'sm:grid-cols-2 xl:grid-cols-3' : 'grid-cols-2 md:grid-cols-3'
                }`}>
                {childNodes.map((node) => (
                  <button
                    type="button"
                    key={node.regionCode}
                    className={`rounded-3xl border px-4 py-4 text-left transition ${
                      viewMode === ACTUAL_MAP_VIEW_MODE
                        ? 'border-default-200 bg-white hover:border-black hover:bg-default-50'
                        : 'border-default-300 bg-white/80 hover:border-black hover:bg-white'
                    }`}
                    onClick={() =>
                      setNavigationPath((current) => [
                        ...current,
                        {
                          regionCode: node.regionCode,
                          regionName: node.regionName,
                          regionType: node.regionType,
                        },
                      ])
                    }>
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="text-base font-semibold">{node.regionName}</p>
                        <p className="mt-1 text-xs uppercase tracking-[0.16em] text-gray-400">
                          {getRegionTypeLabel(node.regionType)}
                        </p>
                      </div>
                      <Chip size="sm" variant="flat">
                        이동
                      </Chip>
                    </div>
                    <p className="mt-3 text-sm leading-6 text-gray-600">
                      {node.resultLabel} · {node.resultValue}
                    </p>
                  </button>
                ))}
              </div>

              {reachedTerminalDepth ? (
                <div className="mt-4 rounded-3xl border border-dashed border-default-300 bg-white/70 p-4">
                  <p className="text-xs font-medium uppercase tracking-[0.16em] text-gray-500">최종 depth 도달</p>
                  <p className="mt-2 text-sm leading-6 text-gray-600">
                    이제 {currentNode.regionName} 기준으로 후보군과 지난 결과를 함께 확인할 수 있습니다. 상단
                    breadcrumb로 언제든 상위 depth로 돌아갈 수 있습니다.
                  </p>
                </div>
              ) : (
                <div className="mt-4 rounded-3xl border border-dashed border-default-300 bg-white/70 p-4">
                  <p className="text-sm leading-6 text-gray-600">
                    {childNodes.length}개 {getRegionContextLabel(childNodes[0]?.regionType ?? 'PROVINCE')}이 준비되어
                    있습니다. 작은 지역이 많은 경우에는 육각형 카토그램으로 전환해 비교 밀도를 높일 수 있습니다.
                  </p>
                </div>
              )}
            </section>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="rounded-2xl border border-default-200 bg-default-50 p-4">
                <p className="text-xs font-medium uppercase tracking-[0.16em] text-gray-500">현재 탐색 위치</p>
                <p className="mt-2 text-lg font-semibold">{activeRegion.regionName}</p>
                <p className="mt-2 text-sm leading-6 text-gray-600">
                  확인된 내 지역은 {regionName} ({getRegionTypeLabel(regionType)} / {regionCode})이며, 현재 후보 목록과
                  상세 패널은 {activeRegion.regionName} 기준 문맥으로 함께 움직입니다.
                </p>
              </div>
              <div className="rounded-2xl border border-default-200 p-4">
                <p className="text-xs font-medium uppercase tracking-[0.16em] text-gray-500">탐색 포인트</p>
                <ul className="mt-3 grid gap-2 text-sm leading-6 text-gray-600">
                  <li>실제 지도: 지리 감각 중심으로 큰 흐름 확인</li>
                  <li>육각형 카토그램: 작은 지역을 같은 비중으로 비교</li>
                  <li>breadcrumb: 전국 / 시도 / 지역 깊이를 빠르게 왕복</li>
                </ul>
              </div>
            </div>
          </CardBody>
        </Card>

        <Card className="border border-default-200 bg-transparent">
          <CardHeader className="px-6 pt-6">
            <div className="space-y-1">
              <h3 className="text-xl font-semibold">{activeRegion.regionName} 후보 목록</h3>
              <p className="text-sm text-gray-500">
                지도에서 선택한 현재 지역 문맥으로 후보와 상세 패널이 함께 갱신됩니다.
              </p>
            </div>
          </CardHeader>
          <CardBody className="grid gap-3 p-6 pt-4">
            {candidates.length ? (
              candidates.map((candidate) => {
                const isSelected = candidate.candidate_id === selectedCandidateId;

                return (
                  <button
                    type="button"
                    key={candidate.candidate_id}
                    className={`rounded-2xl border px-4 py-4 text-left transition ${
                      isSelected ? 'border-black bg-default-50' : 'border-default-200 bg-transparent'
                    }`}
                    onClick={() => setSelectedCandidateId(candidate.candidate_id)}>
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="text-base font-semibold">{candidate.candidate_name}</p>
                        <p className="mt-1 text-sm text-gray-500">{candidate.party_name}</p>
                      </div>
                      {isSelected ? (
                        <Chip size="sm" variant="flat">
                          선택됨
                        </Chip>
                      ) : null}
                    </div>
                  </button>
                );
              })
            ) : (
              <div className="rounded-2xl border border-dashed border-default-300 p-5 text-sm leading-6 text-gray-500">
                이 지역에 연결된 후보 목록이 아직 없습니다.
              </div>
            )}
          </CardBody>
        </Card>
      </section>

      <ElectionDetailPanel
        electionId={electionId}
        candidateId={selectedCandidateId}
        regionName={activeRegion.regionName}
        fallbackCandidateName={selectedCandidate?.candidate_name}
        fallbackManifestoSummary={selectedCandidate?.fallbackSummary}
        fallbackManifestoItems={selectedCandidate?.fallbackItems}
      />
    </section>
  );
}
