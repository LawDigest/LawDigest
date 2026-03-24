'use client';

import { useEffect, useState } from 'react';
import { Button, Card, CardBody, CardHeader, Chip, Spinner } from '@nextui-org/react';
import { ElectionCandidateId, ElectionId } from '@/types';
import {
  useGetElectionCandidates,
  useGetElectionMap,
  useGetElectionOverview,
  useGetElectionRegionPanel,
} from '../apis/queries';
import { getElectionFamilyLabel } from '../utils/electionLabels';
import ElectionDetailPanel from './ElectionDetailPanel';

type PresidentialSection = 'CANDIDATE' | 'REGIONAL';

interface PresidentialElectionViewProps {
  electionId: ElectionId;
}

export default function PresidentialElectionView({ electionId }: PresidentialElectionViewProps) {
  const overviewQuery = useGetElectionOverview(electionId, 'NATIONAL', 'national');
  const candidatesQuery = useGetElectionCandidates(electionId, 'national', null);
  const mapQuery = useGetElectionMap(electionId, 'PROVINCE', 'national', 'RESULT');

  const [activeSection, setActiveSection] = useState<PresidentialSection>('CANDIDATE');
  const [selectedCandidateId, setSelectedCandidateId] = useState<ElectionCandidateId | null>(null);
  const [selectedRegionCode, setSelectedRegionCode] = useState<string | null>(null);

  const overview = overviewQuery.data?.data;
  const candidates = candidatesQuery.data?.data?.candidates ?? [];
  const regions = mapQuery.data?.data?.regions ?? [];
  const selectedRegionPanelQuery = useGetElectionRegionPanel(
    electionId,
    'PROVINCE',
    selectedRegionCode ?? 'national',
    null,
  );
  const selectedRegionPanel = selectedRegionPanelQuery.data?.data;

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

  useEffect(() => {
    if (!regions.length) {
      setSelectedRegionCode(null);
      return;
    }

    setSelectedRegionCode((current) => {
      if (current && regions.some(({ region_code }) => region_code === current)) {
        return current;
      }

      return regions[0].region_code;
    });
  }, [regions]);

  const selectedCandidate =
    candidates.find(({ candidate_id }) => candidate_id === selectedCandidateId) ?? candidates[0] ?? null;
  const selectedRegion = regions.find(({ region_code }) => region_code === selectedRegionCode) ?? regions[0] ?? null;

  const isLoading =
    overviewQuery.isLoading || candidatesQuery.isLoading || mapQuery.isLoading || selectedRegionPanelQuery.isLoading;

  if (isLoading) {
    return (
      <Card className="border border-default-200 bg-transparent">
        <CardBody className="flex min-h-[360px] items-center justify-center">
          <Spinner color="default" label="대통령 선거 정보를 불러오는 중입니다." />
        </CardBody>
      </Card>
    );
  }

  return (
    <section className="grid gap-6">
      <Card className="overflow-hidden border border-default-200 bg-transparent">
        <CardBody className="grid gap-4 bg-gradient-to-br from-amber-50 via-white to-sky-50 p-6 md:grid-cols-[minmax(0,1.2fr)_minmax(0,0.8fr)] md:items-end">
          <div className="space-y-3">
            <div className="flex flex-wrap items-center gap-2">
              <Chip variant="flat">{getElectionFamilyLabel('president')}</Chip>
              {overview?.ui_template ? <Chip variant="bordered">{overview.ui_template}</Chip> : null}
              <Chip variant="bordered">후보자 중심</Chip>
            </div>
            <div className="space-y-1">
              <h2 className="text-3xl font-semibold tracking-tight">
                {overview?.default_result_card.title ?? '대통령 선거 후보자 중심 보기'}
              </h2>
              <p className="max-w-2xl text-sm leading-6 text-gray-500">
                후보자 비교와 지역 결과를 같은 화면에서 오가며 볼 수 있도록 구성했습니다. 공약은 후보 상세 섹션 안에서
                바로 확인합니다.
              </p>
            </div>
          </div>

          <div className="grid gap-3 rounded-3xl border border-white/70 bg-white/80 p-4 shadow-sm">
            <div className="flex items-center justify-between gap-3">
              <p className="text-xs font-medium uppercase tracking-[0.16em] text-gray-500">선거 모드</p>
              <Chip size="sm" variant="flat">
                {activeSection === 'CANDIDATE' ? '후보자 보기' : '지역 결과 보기'}
              </Chip>
            </div>
            <div className="flex flex-wrap gap-2">
              <Button
                size="sm"
                radius="lg"
                variant={activeSection === 'CANDIDATE' ? 'solid' : 'flat'}
                aria-pressed={activeSection === 'CANDIDATE'}
                onClick={() => setActiveSection('CANDIDATE')}>
                후보자 보기
              </Button>
              <Button
                size="sm"
                radius="lg"
                variant={activeSection === 'REGIONAL' ? 'solid' : 'flat'}
                aria-pressed={activeSection === 'REGIONAL'}
                onClick={() => setActiveSection('REGIONAL')}>
                지역 결과 보기
              </Button>
            </div>
          </div>
        </CardBody>
      </Card>

      {activeSection === 'CANDIDATE' ? (
        <section className="grid gap-6 xl:grid-cols-[minmax(0,0.92fr)_minmax(0,1.08fr)]">
          <Card className="border border-default-200 bg-transparent">
            <CardHeader className="flex flex-col items-start gap-2 p-6">
              <div className="space-y-1">
                <h3 className="text-xl font-semibold">후보자 보기</h3>
                <p className="text-sm leading-6 text-gray-500">
                  후보를 눌러 공약과 기본 정보를 확인하고, 상세 패널에서 공약을 이어서 봅니다.
                </p>
              </div>
            </CardHeader>
            <CardBody className="grid gap-3 p-6 pt-0">
              {candidates.map((candidate) => {
                const isSelected = candidate.candidate_id === selectedCandidateId;

                return (
                  <button
                    key={candidate.candidate_id}
                    type="button"
                    className={`rounded-2xl border px-4 py-4 text-left transition ${
                      isSelected
                        ? 'border-black bg-white shadow-sm'
                        : 'border-default-200 bg-transparent hover:bg-default-50'
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
                    <p className="mt-3 text-sm leading-6 text-gray-600">
                      전국 단위 후보 공약을 상세 패널에서 확인합니다.
                    </p>
                  </button>
                );
              })}
            </CardBody>
          </Card>

          <ElectionDetailPanel
            electionId={electionId}
            candidateId={selectedCandidateId}
            regionName="전국"
            fallbackCandidateName={selectedCandidate?.candidate_name}
          />
        </section>
      ) : (
        <section className="grid gap-6 xl:grid-cols-[minmax(0,1.08fr)_minmax(0,0.92fr)]">
          <Card className="border border-default-200 bg-transparent">
            <CardHeader className="flex flex-col items-start gap-2 p-6">
              <div className="space-y-1">
                <h3 className="text-xl font-semibold">지역 결과 보기</h3>
                <p className="text-sm leading-6 text-gray-500">
                  시도별 결과를 눌러 전국 흐름을 비교합니다. 선택된 지역은 우측 요약 카드에 반영됩니다.
                </p>
              </div>
            </CardHeader>
            <CardBody className="grid gap-3 p-6 pt-0 sm:grid-cols-2 xl:grid-cols-3">
              {regions.map((region) => {
                const isSelected = region.region_code === selectedRegionCode;

                return (
                  <button
                    key={region.region_code}
                    type="button"
                    className={`rounded-2xl border px-4 py-4 text-left transition ${
                      isSelected
                        ? 'border-black bg-white shadow-sm'
                        : 'border-default-200 bg-transparent hover:bg-default-50'
                    }`}
                    onClick={() => setSelectedRegionCode(region.region_code)}>
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="text-base font-semibold">{region.region_name}</p>
                        <p className="mt-1 text-sm text-gray-500">{region.value}</p>
                      </div>
                      {isSelected ? (
                        <Chip size="sm" variant="flat">
                          선택됨
                        </Chip>
                      ) : null}
                    </div>
                  </button>
                );
              })}
            </CardBody>
          </Card>

          <div className="grid gap-4">
            <Card className="border border-default-200 bg-transparent">
              <CardHeader className="flex flex-col items-start gap-2 p-6">
                <p className="text-sm font-medium text-gray-500">선택된 지역</p>
                <div>
                  <h3 className="text-2xl font-semibold">
                    {selectedRegionPanel?.region_name ?? selectedRegion?.region_name ?? '지역 결과를 선택하세요'}
                  </h3>
                  <p className="mt-1 text-sm text-gray-500">
                    {selectedRegionPanel?.result_card.title ??
                      selectedRegion?.value ??
                      '지역별 득표 흐름과 후보 우세를 비교할 수 있습니다.'}
                  </p>
                </div>
              </CardHeader>
              <CardBody className="space-y-4 p-6 pt-0">
                <div className="rounded-2xl border border-default-200 bg-default-50 p-4">
                  <p className="text-xs font-medium uppercase tracking-[0.16em] text-gray-500">상세 결과 카드</p>
                  <p className="mt-3 text-lg font-semibold">
                    {selectedRegionPanel?.result_card.title ??
                      overview?.default_result_card.title ??
                      '전국 개요 정보를 불러오는 중입니다.'}
                  </p>
                  <p className="mt-3 text-sm leading-6 text-gray-600">
                    {selectedRegionPanel
                      ? `${selectedRegionPanel.region_name}에서 ${selectedRegion?.value ?? '지역별 흐름'}가 반영된 상세 결과입니다.`
                      : '지역 카드를 누르면 결과 요약이 바뀌도록 구성했습니다.'}
                  </p>
                </div>
                <div className="rounded-2xl border border-dashed border-default-300 p-4 text-sm leading-6 text-gray-500">
                  {selectedRegionPanel
                    ? `${selectedRegionPanel.region_name} 기준으로 공약과 득표 흐름을 함께 볼 수 있습니다.`
                    : '지역 카드를 누르면 결과 요약이 바뀌도록 구성했습니다.'}
                </div>
              </CardBody>
            </Card>

            <Card className="border border-default-200 bg-transparent">
              <CardHeader className="px-6 pt-6">
                <div className="space-y-1">
                  <p className="text-sm font-medium text-gray-500">현재 분류</p>
                  <h4 className="text-lg font-semibold">시도별 결과 비교</h4>
                </div>
              </CardHeader>
              <CardBody className="px-6 pb-6 pt-0 text-sm leading-6 text-gray-600">
                {regions.length ? (
                  <p>
                    현재는 {regions.length}개의 시도 결과가 준비되어 있습니다. 선택한 지역의 상세 결과 카드가 우측
                    패널에 반영됩니다.
                  </p>
                ) : (
                  <p>지역 결과 데이터를 불러오는 중입니다.</p>
                )}
              </CardBody>
            </Card>
          </div>
        </section>
      )}
    </section>
  );
}
