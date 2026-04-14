'use client';

import { useEffect, useMemo, useState } from 'react';
import { Line } from 'react-chartjs-2';
import { Chart as ChartJS, CategoryScale, LinearScale, LineElement, PointElement, Tooltip, Legend } from 'chart.js';
import {
  ElectionPollCandidateResponse,
  ElectionPollLatestSurvey,
  ElectionPollOverviewResponse,
  ElectionPollSnapshotItem,
} from '@/types';
import {
  useGetElectionPollCandidate,
  useGetElectionPollOverview,
  useGetElectionPollParty,
  useGetElectionPollRegion,
} from '../apis/queries';
import { aggregatePartySnapshots, isUndecidedLikePartyName, normalizePartyName } from '../utils/partyName';
import { ConfirmedRegion } from './ElectionMapShell';
import PartyRingSelector from './shared/PartyRingSelector';
import DistrictMapPicker, { SelectedRegion } from './shared/DistrictMapPicker';
import PollRegionPanel from './PollRegionPanel';
import ElectionCandidatePollPanel from './ElectionCandidatePollPanel';
import SubTabBar from './shared/SubTabBar';

ChartJS.register(CategoryScale, LinearScale, LineElement, PointElement, Tooltip, Legend);

type PollSubView = 'all' | 'party' | 'region' | 'candidate';
type TimeFilter = 'all' | '3m' | '1m';

const SUB_TABS: { key: PollSubView; label: string }[] = [
  { key: 'all', label: '전체' },
  { key: 'party', label: '정당별' },
  { key: 'region', label: '지역별' },
  { key: 'candidate', label: '후보자별' },
];

function getColorForName(name: string) {
  const normalizedName = normalizePartyName(name);

  if (normalizedName.includes('더불어민주')) return '#152484';
  if (normalizedName.includes('국민의힘')) return '#C9151E';
  if (normalizedName.includes('개혁신당')) return '#FF7210';
  if (normalizedName.includes('조국')) return '#6A3FA0';
  if (normalizedName === 'undecided') return '#999999';
  return '#5b6475';
}

function formatCompactDate(dateText: string) {
  const parsed = new Date(dateText);
  if (Number.isNaN(parsed.getTime())) {
    return dateText;
  }

  return `${parsed.getMonth() + 1}/${parsed.getDate()}`;
}

function filterOutUndecided<T extends { label: string }>(items: T[]) {
  return items.filter((item) => !isUndecidedLikePartyName(item.label));
}

function mapSurveySnapshot(snapshot: ElectionPollSnapshotItem[]) {
  return filterOutUndecided(
    aggregatePartySnapshots(snapshot).map((item) => ({
      label: item.party_name,
      pct: item.percentage,
      color: getColorForName(item.party_name),
    })),
  );
}

function getTrendWindow(points: ElectionPollOverviewResponse['party_trend'], filter: TimeFilter) {
  if (filter === 'all' || points.length === 0) {
    return points;
  }

  const latestDate = points.reduce((latest, point) => {
    const current = new Date(point.survey.survey_end_date);
    if (Number.isNaN(current.getTime())) {
      return latest;
    }

    return current > latest ? current : latest;
  }, new Date(points[0].survey.survey_end_date));

  if (Number.isNaN(latestDate.getTime())) {
    return points;
  }

  const cutoff = new Date(latestDate);
  cutoff.setMonth(cutoff.getMonth() - (filter === '1m' ? 1 : 3));

  return points.filter((point) => {
    const current = new Date(point.survey.survey_end_date);
    return !Number.isNaN(current.getTime()) && current >= cutoff;
  });
}

interface StatCardProps {
  label: string;
  value: string;
  sub: string;
  changeLabel?: string;
  positive?: boolean;
  accentColor?: string;
  icon: string;
}

function StatCard({ label, value, sub, changeLabel, positive, accentColor = '#152484', icon }: StatCardProps) {
  return (
    <div className="flex min-w-[220px] flex-1 flex-col gap-2 rounded-2xl border border-gray-1 bg-white p-4 dark:border-dark-l dark:bg-dark-pb">
      <div className="flex items-center justify-between">
        <span className="material-symbols-outlined text-xl" style={{ color: accentColor }}>
          {icon}
        </span>
        {changeLabel ? (
          <span
            className="rounded-full px-2 py-0.5 text-[10px] font-bold"
            style={{
              color: positive ? '#152484' : '#C9151E',
              backgroundColor: positive ? '#E8EDFF' : '#FFEAEA',
            }}>
            {changeLabel}
          </span>
        ) : null}
      </div>
      <p className="text-[10px] font-semibold uppercase tracking-widest text-gray-2">{label}</p>
      <p className="text-3xl font-black leading-none text-gray-4 dark:text-white">{value}</p>
      <p className="text-[11px] text-gray-2">{sub}</p>
    </div>
  );
}

function CandidateBar({ label, pct, color, max }: { label: string; pct: number; color: string; max: number }) {
  const width = max > 0 ? (pct / max) * 100 : 0;

  return (
    <div className="flex items-center gap-2">
      <span className="w-[72px] shrink-0 truncate text-[12px] text-gray-3 dark:text-gray-1">{label}</span>
      <div className="h-2 flex-1 overflow-hidden rounded-full bg-default-100 dark:bg-dark-b">
        <div className="h-full rounded-full" style={{ width: `${width}%`, backgroundColor: color }} />
      </div>
      <span className="w-10 text-right text-[12px] font-bold tabular-nums text-gray-4 dark:text-white">{pct}%</span>
    </div>
  );
}

function SnapshotBar({ label, percentage, color }: { label: string; percentage: number; color: string }) {
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-[11px]">
        <span className="font-medium text-gray-3 dark:text-gray-1">{label}</span>
        <span className="font-bold text-gray-4 dark:text-white">{percentage}%</span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-default-100 dark:bg-dark-b">
        <div className="h-full rounded-full" style={{ width: `${percentage}%`, backgroundColor: color }} />
      </div>
    </div>
  );
}

function AgencyPollCard({ survey }: { survey: ElectionPollLatestSurvey }) {
  const [expanded, setExpanded] = useState(false);
  const results = mapSurveySnapshot(survey.snapshot);
  const visibleResults = expanded ? results : results.slice(0, 3);
  const maxPct = Math.max(...results.map((result) => result.pct), 1);

  return (
    <div className="space-y-3 rounded-2xl border border-gray-1 bg-white p-4 dark:border-dark-l dark:bg-dark-pb">
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-default-100 dark:bg-dark-b">
            <span className="text-center text-[9px] font-black leading-tight text-gray-3 dark:text-gray-1">
              {survey.pollster.slice(0, 3)}
            </span>
          </div>
          <div>
            <p className="text-[13px] font-bold leading-tight text-gray-4 dark:text-white">{survey.pollster}</p>
            <p className="text-[10px] text-gray-2">{survey.sponsor} 의뢰</p>
          </div>
        </div>
        <div className="shrink-0 text-right">
          <p className="text-[10px] font-semibold text-gray-3 dark:text-gray-1">{survey.survey_end_date}</p>
          <p className="text-[10px] text-gray-2">오차 {survey.margin_of_error}</p>
        </div>
      </div>

      <p className="rounded-lg bg-default-100 px-3 py-2 text-[11px] font-semibold text-gray-3 dark:bg-dark-b dark:text-gray-1">
        {survey.question_title}
      </p>

      <div className="space-y-2">
        {visibleResults.map((result) => (
          <CandidateBar key={result.label} label={result.label} pct={result.pct} color={result.color} max={maxPct} />
        ))}
      </div>

      <div className="flex items-center justify-between pt-1">
        <span className="text-[10px] text-gray-2">표본 {survey.sample_size.toLocaleString()}명</span>
        {results.length > 3 ? (
          <button
            type="button"
            onClick={() => setExpanded((value) => !value)}
            className="flex items-center gap-0.5 text-[11px] font-semibold text-primary-3 dark:text-primary-2">
            {expanded ? '접기' : '더보기'}
            <span className="material-symbols-outlined text-[14px]">{expanded ? 'expand_less' : 'expand_more'}</span>
          </button>
        ) : null}
      </div>
    </div>
  );
}

function AgencyPollTable({ surveys }: { surveys: ElectionPollLatestSurvey[] }) {
  return (
    <div className="overflow-hidden rounded-2xl border border-gray-1 bg-white dark:border-dark-l dark:bg-dark-pb">
      <div className="flex items-center justify-between border-b border-gray-1 px-5 py-4 dark:border-dark-l">
        <h3 className="text-[14px] font-bold text-gray-4 dark:text-white">최신 여론조사</h3>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left">
          <thead>
            <tr className="border-b border-gray-1/50 bg-default-50 dark:border-dark-l dark:bg-dark-b">
              <th className="whitespace-nowrap px-5 py-3 text-[10px] font-bold uppercase tracking-widest text-gray-2">
                조사기관
              </th>
              <th className="px-5 py-3 text-[10px] font-bold uppercase tracking-widest text-gray-2">주요 질문</th>
              <th className="whitespace-nowrap px-5 py-3 text-[10px] font-bold uppercase tracking-widest text-gray-2">
                1위
              </th>
              <th className="whitespace-nowrap px-5 py-3 text-[10px] font-bold uppercase tracking-widest text-gray-2">
                2위
              </th>
              <th className="whitespace-nowrap px-5 py-3 text-[10px] font-bold uppercase tracking-widest text-gray-2">
                발표일
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-1/50 dark:divide-dark-l">
            {surveys.map((survey) => {
              const results = [...mapSurveySnapshot(survey.snapshot)].sort((left, right) => right.pct - left.pct);
              const first = results[0];
              const second = results[1];
              const maxPct = first?.pct ?? 1;

              return (
                <tr
                  key={survey.registration_number}
                  className="transition-colors hover:bg-default-50 dark:hover:bg-dark-b/50">
                  <td className="whitespace-nowrap px-5 py-4">
                    <p className="text-[12px] font-bold leading-tight text-gray-4 dark:text-white">{survey.pollster}</p>
                    <p className="mt-0.5 text-[10px] text-gray-2">{survey.sponsor} 의뢰</p>
                  </td>
                  <td className="max-w-[180px] px-5 py-4 md:max-w-[240px]">
                    <p className="line-clamp-2 text-[11px] leading-tight text-gray-3 dark:text-gray-1">
                      {survey.question_title}
                    </p>
                    <p className="mt-0.5 text-[10px] text-gray-2">
                      n={survey.sample_size.toLocaleString()} · {survey.margin_of_error}
                    </p>
                  </td>
                  <td className="whitespace-nowrap px-5 py-4">
                    {first ? (
                      <>
                        <div className="flex items-center gap-2">
                          <div className="h-1.5 w-16 overflow-hidden rounded-full bg-default-100 dark:bg-dark-b">
                            <div
                              className="h-full rounded-full"
                              style={{ width: `${(first.pct / maxPct) * 100}%`, backgroundColor: first.color }}
                            />
                          </div>
                          <span className="text-[12px] font-bold tabular-nums text-gray-4 dark:text-white">
                            {first.pct}%
                          </span>
                        </div>
                        <p className="mt-0.5 max-w-[100px] truncate text-[10px] text-gray-2">{first.label}</p>
                      </>
                    ) : (
                      <span className="text-[11px] text-gray-2">—</span>
                    )}
                  </td>
                  <td className="whitespace-nowrap px-5 py-4">
                    {second ? (
                      <>
                        <div className="flex items-center gap-2">
                          <div className="h-1.5 w-16 overflow-hidden rounded-full bg-default-100 dark:bg-dark-b">
                            <div
                              className="h-full rounded-full"
                              style={{ width: `${(second.pct / maxPct) * 100}%`, backgroundColor: second.color }}
                            />
                          </div>
                          <span className="text-[12px] font-bold tabular-nums text-gray-4 dark:text-white">
                            {second.pct}%
                          </span>
                        </div>
                        <p className="mt-0.5 max-w-[100px] truncate text-[10px] text-gray-2">{second.label}</p>
                      </>
                    ) : (
                      <span className="text-[11px] text-gray-2">—</span>
                    )}
                  </td>
                  <td className="whitespace-nowrap px-5 py-4">
                    <p className="text-[11px] font-semibold text-gray-3 dark:text-gray-1">{survey.survey_end_date}</p>
                    <p className="mt-0.5 text-[10px] text-gray-2">{survey.registration_number}</p>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function OverviewView({
  regionName,
  data,
  candidateData,
}: {
  regionName: string;
  data: ElectionPollOverviewResponse | undefined;
  candidateData: ElectionPollCandidateResponse | undefined;
}) {
  const [timeFilter, setTimeFilter] = useState<TimeFilter>('all');

  if (!data) {
    return <p className="px-4 py-8 text-sm text-gray-2">여론조사 데이터를 불러오지 못했습니다.</p>;
  }

  const filteredTrend = getTrendWindow(data.party_trend, timeFilter);
  const normalizedTrend = filteredTrend.map((point) => ({
    ...point,
    snapshot: aggregatePartySnapshots(point.snapshot),
  }));
  const trendLabels = normalizedTrend.map((point) => formatCompactDate(point.survey.survey_end_date));
  const partyNames = Array.from(
    new Set(normalizedTrend.flatMap((point) => point.snapshot.map((snapshot) => snapshot.party_name))),
  );
  const latestSurvey = data.latest_surveys[0];
  const latestSnapshot = latestSurvey ? mapSurveySnapshot(latestSurvey.snapshot) : [];
  const candidateSnapshot = candidateData?.latest_snapshot ?? [];
  const leadCandidates = candidateSnapshot.slice(0, Math.ceil(candidateSnapshot.length / 2));
  const trailingCandidates = candidateSnapshot.slice(Math.ceil(candidateSnapshot.length / 2));
  const leadMax = Math.max(...leadCandidates.map((item) => item.percentage), 1);
  const trailingMax = Math.max(...trailingCandidates.map((item) => item.percentage), 1);
  const leadingPartyName = normalizePartyName(data.leading_party?.party_name);
  const runnerUpPartyName = normalizePartyName(data.leading_party?.runner_up_party);

  return (
    <div className="space-y-5 px-4 pb-8 pt-3">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-1.5">
          <span className="material-symbols-outlined text-[16px] text-primary-3 dark:text-primary-2">location_on</span>
          <span className="text-[13px] font-bold text-gray-4 dark:text-white">{regionName}</span>
        </div>
        <div className="flex gap-0.5 rounded-lg bg-default-100 p-0.5 dark:bg-dark-b">
          {(
            [
              ['all', '전체'],
              ['3m', '3개월'],
              ['1m', '1개월'],
            ] as [TimeFilter, string][]
          ).map(([key, label]) => (
            <button
              key={key}
              type="button"
              onClick={() => setTimeFilter(key)}
              className={`rounded-md px-2.5 py-1 text-[11px] font-bold transition-all ${
                timeFilter === key ? 'bg-white text-gray-4 shadow-sm dark:bg-dark-pb dark:text-white' : 'text-gray-2'
              }`}>
              {label}
            </button>
          ))}
        </div>
      </div>

      <div className="-mx-4 flex gap-3 overflow-x-auto px-4 pb-1 md:mx-0 md:grid md:grid-cols-3 md:overflow-visible md:px-0">
        <StatCard
          icon="bar_chart"
          label="1위 정당 지지율"
          value={`${data.leading_party?.percentage ?? 0}%`}
          sub={`${leadingPartyName || '데이터 없음'} · 최신 조사 기준`}
          changeLabel={data.leading_party?.runner_up_party ? `${data.leading_party.gap}%p 격차` : undefined}
          positive
          accentColor={getColorForName(leadingPartyName)}
        />
        <StatCard
          icon="trending_down"
          label="1·2위 지지율 격차"
          value={`${data.leading_party?.gap ?? 0}%p`}
          sub={`${leadingPartyName || '데이터 없음'} vs ${runnerUpPartyName || '후속 정당 없음'}`}
          changeLabel={data.leading_party?.runner_up_party ? '최신 기준' : undefined}
          positive
          accentColor="#555"
        />
        <StatCard
          icon="group"
          label="부동층 (없음+모름)"
          value={`${data.leading_party?.undecided ?? 0}%`}
          sub="지지정당 없음·잘모름 합산"
          accentColor="#999"
        />
      </div>

      <div className="space-y-4 md:grid md:grid-cols-5 md:gap-4 md:space-y-0">
        <div className="rounded-3xl border border-gray-1/60 bg-white p-5 shadow-sm dark:border-dark-l dark:bg-dark-pb md:col-span-3">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h3 className="text-[14px] font-semibold tracking-tight text-gray-4 dark:text-white">정당지지율 추이</h3>
              <p className="mt-0.5 text-[10px] text-gray-2">실제 조사 응답 기준</p>
            </div>
            <div className="flex flex-wrap justify-end gap-x-3 gap-y-1.5">
              {partyNames.map((partyName) => (
                <span
                  key={partyName}
                  className="flex items-center gap-1.5 text-[10px] font-medium text-gray-3 dark:text-gray-1">
                  <span
                    className="inline-block h-1.5 w-5 rounded-full"
                    style={{ backgroundColor: getColorForName(partyName) }}
                  />
                  {partyName}
                </span>
              ))}
            </div>
          </div>
          <div className="h-[210px]">
            <Line
              data={{
                labels: trendLabels,
                datasets: partyNames.map((partyName) => ({
                  label: partyName,
                  data: normalizedTrend.map(
                    (point) => point.snapshot.find((snapshot) => snapshot.party_name === partyName)?.percentage ?? null,
                  ),
                  borderColor: getColorForName(partyName),
                  backgroundColor: 'transparent',
                  tension: 0.35,
                  pointRadius: 3,
                  pointBackgroundColor: getColorForName(partyName),
                  pointBorderColor: '#ffffff',
                  pointBorderWidth: 1.5,
                  pointHoverRadius: 5,
                  pointHoverBackgroundColor: getColorForName(partyName),
                  pointHoverBorderColor: '#ffffff',
                  pointHoverBorderWidth: 2,
                  borderWidth: 2,
                  fill: false,
                  spanGaps: true,
                })),
              }}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                interaction: { mode: 'index', intersect: false },
                plugins: {
                  legend: { display: false },
                },
                scales: {
                  y: {
                    min: 0,
                    max: 65,
                    grid: { display: false },
                    border: { display: false },
                    ticks: {
                      callback: (value) => `${value}%`,
                      font: { size: 10 },
                      color: '#94a3b8',
                      padding: 6,
                      stepSize: 20,
                    },
                  },
                  x: {
                    grid: {
                      display: true,
                      color: 'rgba(148,163,184,0.2)',
                      lineWidth: 1,
                    },
                    border: { display: false },
                    ticks: {
                      font: { size: 10 },
                      color: '#94a3b8',
                      maxRotation: 0,
                      maxTicksLimit: 7,
                      padding: 6,
                    },
                  },
                },
              }}
            />
          </div>
        </div>

        <div className="rounded-2xl border border-gray-1 bg-white p-4 dark:border-dark-l dark:bg-dark-pb md:col-span-2">
          <h3 className="mb-3 text-[13px] font-bold text-gray-4 dark:text-white">현재 정당지지율</h3>
          <div className="space-y-2.5">
            {latestSnapshot.map((snapshot) => (
              <SnapshotBar
                key={snapshot.label}
                label={snapshot.label}
                percentage={snapshot.pct}
                color={snapshot.color}
              />
            ))}
          </div>
          {latestSurvey ? (
            <p className="mt-3 text-[10px] text-gray-2">
              {latestSurvey.survey_end_date} · 표본 {latestSurvey.sample_size.toLocaleString()}명
            </p>
          ) : null}
        </div>
      </div>

      {candidateSnapshot.length > 0 ? (
        <div className="space-y-4 md:grid md:grid-cols-2 md:gap-4 md:space-y-0">
          <div className="rounded-2xl border border-gray-1 bg-white p-4 dark:border-dark-l dark:bg-dark-pb">
            <div className="mb-3 flex items-center gap-2">
              <span className="inline-block h-3 w-3 rounded-full bg-[#152484]" />
              <h3 className="text-[13px] font-bold text-gray-4 dark:text-white">선두권 후보 경쟁도</h3>
            </div>
            <div className="space-y-2">
              {leadCandidates.map((candidate) => (
                <CandidateBar
                  key={candidate.candidate_name}
                  label={candidate.candidate_name}
                  pct={candidate.percentage}
                  color={getColorForName(candidate.candidate_name)}
                  max={leadMax}
                />
              ))}
            </div>
            {candidateData?.basis_question_kind ? (
              <p className="mt-3 text-[10px] text-gray-2">기준 질문: {candidateData.basis_question_kind}</p>
            ) : null}
          </div>

          <div className="rounded-2xl border border-gray-1 bg-white p-4 dark:border-dark-l dark:bg-dark-pb">
            <div className="mb-3 flex items-center gap-2">
              <span className="inline-block h-3 w-3 rounded-full bg-[#C9151E]" />
              <h3 className="text-[13px] font-bold text-gray-4 dark:text-white">후속 후보 비교</h3>
            </div>
            <div className="space-y-2">
              {(trailingCandidates.length > 0 ? trailingCandidates : leadCandidates).map((candidate) => (
                <CandidateBar
                  key={candidate.candidate_name}
                  label={candidate.candidate_name}
                  pct={candidate.percentage}
                  color={getColorForName(candidate.candidate_name)}
                  max={trailingCandidates.length > 0 ? trailingMax : leadMax}
                />
              ))}
            </div>
            {candidateData?.selected_candidate ? (
              <p className="mt-3 text-[10px] text-gray-2">선택 후보: {candidateData.selected_candidate}</p>
            ) : null}
          </div>
        </div>
      ) : null}

      <AgencyPollTable surveys={data.latest_surveys} />

      <div className="space-y-3">
        {data.latest_surveys.map((survey) => (
          <AgencyPollCard key={survey.registration_number} survey={survey} />
        ))}
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
  const regionQuery = useGetElectionPollRegion(
    selectedElectionId,
    regionCode,
    (subView === 'all' || subView === 'region') && !!regionCode,
  );
  const candidateQuery = useGetElectionPollCandidate(
    selectedElectionId,
    regionCode,
    selectedCandidate,
    (subView === 'all' || subView === 'candidate') && !!regionCode,
  );

  const availableParties = useMemo(
    () =>
      aggregatePartySnapshots(overviewQuery.data?.data?.latest_surveys?.[0]?.snapshot ?? [])
        ?.filter((snapshot) => snapshot.party_name !== 'undecided')
        .map((snapshot) => ({ name: snapshot.party_name, color: getColorForName(snapshot.party_name) })) ?? [],
    [overviewQuery.data?.data?.latest_surveys],
  );

  useEffect(() => {
    if (!selectedParty && availableParties.length > 0) {
      setSelectedParty(availableParties[0].name);
    }
  }, [availableParties, selectedParty]);

  return (
    <div className="flex flex-col">
      <SubTabBar tabs={SUB_TABS} active={subView} onChange={setSubView} />

      {subView === 'all' && (
        <OverviewView
          regionName={regionName}
          data={overviewQuery.data?.data}
          candidateData={candidateQuery.data?.data}
        />
      )}

      {subView === 'party' && (
        <div className="space-y-4 pb-6">
          <PartyRingSelector parties={availableParties} selected={selectedParty} onSelect={setSelectedParty} />
          {partyQuery.data?.data ? (
            <div className="space-y-4 px-4">
              <div className="rounded-2xl border border-gray-1 bg-white p-4 dark:border-dark-l dark:bg-dark-pb">
                <h3 className="mb-3 text-[13px] font-bold text-gray-4 dark:text-white">
                  {normalizePartyName(partyQuery.data.data.selected_party)} 지역별 지지율
                </h3>
                <div className="space-y-3">
                  {partyQuery.data.data.regional_distribution.map((item) => (
                    <SnapshotBar
                      key={item.region_name}
                      label={item.region_name}
                      percentage={item.percentage}
                      color={getColorForName(normalizePartyName(partyQuery.data!.data.selected_party))}
                    />
                  ))}
                </div>
              </div>

              <div className="rounded-2xl border border-gray-1 bg-white p-4 dark:border-dark-l dark:bg-dark-pb">
                <h3 className="mb-3 text-[13px] font-bold text-gray-4 dark:text-white">정당 추이</h3>
                <div className="h-[220px]">
                  <Line
                    data={{
                      labels: partyQuery.data.data.trend_series.map((item) => item.survey.survey_end_date),
                      datasets: [
                        {
                          label: normalizePartyName(partyQuery.data.data.selected_party),
                          data: partyQuery.data.data.trend_series.map((item) => item.percentage),
                          borderColor: getColorForName(normalizePartyName(partyQuery.data.data.selected_party)),
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
          {selectedRegion?.regionName ? (
            <div className="mt-4">
              <PollRegionPanel response={regionQuery.data?.data} />
            </div>
          ) : null}
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
          {selectedRegion?.regionName ? (
            <div className="mt-4">
              <ElectionCandidatePollPanel
                response={candidateQuery.data?.data}
                onSelectCandidate={(candidate) => setSelectedCandidate(candidate)}
              />
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
}
