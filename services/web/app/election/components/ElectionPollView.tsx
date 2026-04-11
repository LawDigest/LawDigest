'use client';

import { useEffect, useState } from 'react';
import { Line } from 'react-chartjs-2';
import { Chart as ChartJS, CategoryScale, LinearScale, LineElement, PointElement, Tooltip, Legend } from 'chart.js';
import { ElectionPollOverviewResponse } from '@/types';
import {
  useGetElectionPollCandidate,
  useGetElectionPollOverview,
  useGetElectionPollParty,
  useGetElectionPollRegion,
} from '../apis/queries';
import { ConfirmedRegion } from './ElectionMapShell';
import PartyRingSelector from './shared/PartyRingSelector';
import DistrictMapPicker, { SelectedRegion } from './shared/DistrictMapPicker';
import PollRegionPanel from './PollRegionPanel';
import ElectionCandidatePollPanel from './ElectionCandidatePollPanel';
import SubTabBar from './shared/SubTabBar';

ChartJS.register(CategoryScale, LinearScale, LineElement, PointElement, Tooltip, Legend);

type PollSubView = 'all' | 'party' | 'region' | 'candidate';

const SUB_TABS: { key: PollSubView; label: string }[] = [
  { key: 'all', label: '전체' },
  { key: 'party', label: '정당별' },
  { key: 'region', label: '지역별' },
  { key: 'candidate', label: '후보자별' },
];

function getColorForName(name: string) {
  if (name.includes('더불어민주')) return '#152484';
  if (name.includes('국민의힘')) return '#C9151E';
  if (name.includes('개혁신당')) return '#FF7210';
  if (name.includes('조국')) return '#6A3FA0';
  if (name === 'undecided') return '#999999';
  return '#5b6475';
}

function SnapshotBar({ label, percentage, color }: { label: string; percentage: number; color: string }) {
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-[11px]">
        <span className="font-medium text-gray-3 dark:text-gray-1">{label}</span>
        <span className="font-bold text-gray-4 dark:text-white">{percentage}%</span>
      </div>
      <div className="h-2 w-full rounded-full bg-default-100 dark:bg-dark-b overflow-hidden">
        <div className="h-full rounded-full" style={{ width: `${percentage}%`, backgroundColor: color }} />
      </div>
    </div>
  );
}

function OverviewView({ regionName, data }: { regionName: string; data: ElectionPollOverviewResponse | undefined }) {
  if (!data) {
    return <p className="px-4 py-8 text-sm text-gray-2">여론조사 데이터를 불러오지 못했습니다.</p>;
  }

  const latestSurvey = data.latest_surveys[0];
  const trendLabels = data.party_trend.map((point) => point.survey.survey_end_date);
  const partyNames = Array.from(
    new Set(data.party_trend.flatMap((point) => point.snapshot.map((snapshot) => snapshot.party_name))),
  );

  return (
    <div className="space-y-5 px-4 pb-8 pt-3">
      <div className="flex items-center gap-1.5">
        <span className="material-symbols-outlined text-[16px] text-primary-3 dark:text-primary-2">location_on</span>
        <span className="text-[13px] font-bold text-gray-4 dark:text-white">{regionName}</span>
      </div>

      <div className="grid gap-3 md:grid-cols-3">
        <div className="rounded-2xl border border-gray-1 dark:border-dark-l bg-white dark:bg-dark-pb p-4">
          <p className="text-[10px] font-semibold uppercase tracking-widest text-gray-2">1위 정당</p>
          <p className="mt-2 text-2xl font-black text-gray-4 dark:text-white">
            {data.leading_party?.party_name ?? '데이터 없음'}
          </p>
          <p className="mt-1 text-[12px] text-gray-2">{data.leading_party?.percentage ?? 0}%</p>
        </div>
        <div className="rounded-2xl border border-gray-1 dark:border-dark-l bg-white dark:bg-dark-pb p-4">
          <p className="text-[10px] font-semibold uppercase tracking-widest text-gray-2">격차</p>
          <p className="mt-2 text-2xl font-black text-gray-4 dark:text-white">{data.leading_party?.gap ?? 0}%p</p>
        </div>
        <div className="rounded-2xl border border-gray-1 dark:border-dark-l bg-white dark:bg-dark-pb p-4">
          <p className="text-[10px] font-semibold uppercase tracking-widest text-gray-2">부동층</p>
          <p className="mt-2 text-2xl font-black text-gray-4 dark:text-white">{data.leading_party?.undecided ?? 0}%</p>
        </div>
      </div>

      <div className="rounded-2xl border border-gray-1 dark:border-dark-l bg-white dark:bg-dark-pb p-4">
        <h3 className="mb-3 text-[13px] font-bold text-gray-4 dark:text-white">정당지지율 추이</h3>
        <div className="h-[220px]">
          <Line
            data={{
              labels: trendLabels,
              datasets: partyNames.map((partyName) => ({
                label: partyName,
                data: data.party_trend.map(
                  (point) => point.snapshot.find((snapshot) => snapshot.party_name === partyName)?.percentage ?? null,
                ),
                borderColor: getColorForName(partyName),
                backgroundColor: 'transparent',
                tension: 0.35,
              })),
            }}
            options={{ responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } }}
          />
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="rounded-2xl border border-gray-1 dark:border-dark-l bg-white dark:bg-dark-pb p-4 space-y-3">
          <h3 className="text-[13px] font-bold text-gray-4 dark:text-white">최신 정당 스냅샷</h3>
          {latestSurvey?.snapshot?.map((snapshot) => (
            <SnapshotBar
              key={snapshot.party_name}
              label={snapshot.party_name}
              percentage={snapshot.percentage}
              color={getColorForName(snapshot.party_name)}
            />
          ))}
        </div>

        <div className="rounded-2xl border border-gray-1 dark:border-dark-l bg-white dark:bg-dark-pb p-4 space-y-3">
          <h3 className="text-[13px] font-bold text-gray-4 dark:text-white">최신 조사 리스트</h3>
          {data.latest_surveys.map((survey) => (
            <div
              key={survey.registration_number}
              className="rounded-xl bg-default-50 dark:bg-dark-b px-3 py-2 flex items-center justify-between">
              <div>
                <p className="text-[12px] font-semibold text-gray-4 dark:text-white">{survey.pollster}</p>
                <p className="text-[10px] text-gray-2">
                  {survey.sponsor} · 표본 {survey.sample_size}명 · {survey.margin_of_error}
                </p>
                <p className="text-[10px] text-gray-2">{survey.question_title}</p>
              </div>
              <p className="text-[11px] text-gray-2">{survey.survey_end_date}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

interface ElectionPollViewProps {
  confirmedRegion: ConfirmedRegion | null;
  selectedElectionId: string;
}

export default function ElectionPollView({ confirmedRegion, selectedElectionId }: ElectionPollViewProps) {
  const [subView, setSubView] = useState<PollSubView>('all');
  const [selectedParty, setSelectedParty] = useState<string | null>(null);
  const [selectedCandidate, setSelectedCandidate] = useState<string | null>(null);
  const [selectedRegion, setSelectedRegion] = useState<SelectedRegion | null>(
    confirmedRegion ? { regionCode: confirmedRegion.regionCode, regionName: confirmedRegion.regionName } : null,
  );

  useEffect(() => {
    if (confirmedRegion) {
      setSelectedRegion({ regionCode: confirmedRegion.regionCode, regionName: confirmedRegion.regionName });
    }
  }, [confirmedRegion]);

  const regionCode = selectedRegion?.regionCode ?? confirmedRegion?.regionCode ?? '';
  const regionName = selectedRegion?.regionName ?? confirmedRegion?.regionName ?? '지역 미선택';

  const overviewQuery = useGetElectionPollOverview(selectedElectionId, regionCode, !!regionCode);
  const partyQuery = useGetElectionPollParty(selectedElectionId, selectedParty, !!selectedParty);
  const regionQuery = useGetElectionPollRegion(selectedElectionId, regionCode, subView === 'region' && !!regionCode);
  const candidateQuery = useGetElectionPollCandidate(
    selectedElectionId,
    regionCode,
    selectedCandidate,
    subView === 'candidate' && !!regionCode,
  );

  const availableParties =
    overviewQuery.data?.data?.latest_surveys?.[0]?.snapshot
      ?.filter((snapshot) => snapshot.party_name !== 'undecided')
      .map((snapshot) => ({ name: snapshot.party_name, color: getColorForName(snapshot.party_name) })) ?? [];

  useEffect(() => {
    if (!selectedParty && availableParties.length > 0) {
      setSelectedParty(availableParties[0].name);
    }
  }, [availableParties, selectedParty]);

  return (
    <div className="flex flex-col">
      <SubTabBar tabs={SUB_TABS} active={subView} onChange={setSubView} />

      {subView === 'all' && <OverviewView regionName={regionName} data={overviewQuery.data?.data} />}

      {subView === 'party' && (
        <div className="space-y-4 pb-6">
          <PartyRingSelector parties={availableParties} selected={selectedParty} onSelect={setSelectedParty} />
          {partyQuery.data?.data ? (
            <div className="space-y-4 px-4">
              <div className="rounded-2xl border border-gray-1 dark:border-dark-l bg-white dark:bg-dark-pb p-4">
                <h3 className="mb-3 text-[13px] font-bold text-gray-4 dark:text-white">
                  {partyQuery.data.data.selected_party} 지역별 지지율
                </h3>
                <div className="space-y-3">
                  {partyQuery.data.data.regional_distribution.map((item) => (
                    <SnapshotBar
                      key={item.region_name}
                      label={item.region_name}
                      percentage={item.percentage}
                      color={getColorForName(partyQuery.data!.data.selected_party)}
                    />
                  ))}
                </div>
              </div>

              <div className="rounded-2xl border border-gray-1 dark:border-dark-l bg-white dark:bg-dark-pb p-4">
                <h3 className="mb-3 text-[13px] font-bold text-gray-4 dark:text-white">정당 추이</h3>
                <div className="h-[220px]">
                  <Line
                    data={{
                      labels: partyQuery.data.data.trend_series.map((item) => item.survey.survey_end_date),
                      datasets: [
                        {
                          label: partyQuery.data.data.selected_party,
                          data: partyQuery.data.data.trend_series.map((item) => item.percentage),
                          borderColor: getColorForName(partyQuery.data.data.selected_party),
                          backgroundColor: 'transparent',
                          tension: 0.35,
                        },
                      ],
                    }}
                    options={{ responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } }}
                  />
                </div>
              </div>
            </div>
          ) : (
            <p className="px-4 py-8 text-sm text-gray-2">정당을 선택해 지지율 분포를 확인하세요.</p>
          )}
        </div>
      )}

      {subView === 'region' && (
        <div className="pb-6">
          <DistrictMapPicker selected={selectedRegion} onSelect={setSelectedRegion} label="지역을 선택하세요" />
          {selectedRegion?.regionName && (
            <div className="mt-4">
              <PollRegionPanel response={regionQuery.data?.data} />
            </div>
          )}
        </div>
      )}

      {subView === 'candidate' && (
        <div className="pb-6">
          <DistrictMapPicker
            selected={selectedRegion}
            onSelect={(region) => {
              setSelectedRegion(region);
              setSelectedCandidate(null);
            }}
            label="후보자를 볼 지역을 선택하세요"
          />
          {selectedRegion?.regionName && (
            <div className="mt-4">
              <ElectionCandidatePollPanel
                response={candidateQuery.data?.data}
                onSelectCandidate={(candidate) => setSelectedCandidate(candidate)}
              />
            </div>
          )}
        </div>
      )}
    </div>
  );
}
