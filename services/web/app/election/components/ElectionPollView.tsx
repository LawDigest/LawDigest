// services/web/app/election/components/ElectionPollView.tsx

'use client';

import { useState } from 'react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  LineElement,
  PointElement,
  Tooltip,
  Legend,
  type Plugin,
} from 'chart.js';
import { ConfirmedRegion } from './ElectionMapShell';
import { MOCK_PARTY_POLL_DATA } from '../data/mockPartyPollData';
import { MOCK_POLL_TIMESERIES } from '../data/mockPollTimeseriesData';
import { MOCK_AGENCY_POLLS, POLL_SUMMARY } from '../data/mockAgencyPollsData';
import PartyRingSelector from './shared/PartyRingSelector';
import DistrictMapPicker, { SelectedRegion } from './shared/DistrictMapPicker';
import PollRegionPanel from './PollRegionPanel';
import SubTabBar from './shared/SubTabBar';

ChartJS.register(CategoryScale, LinearScale, LineElement, PointElement, Tooltip, Legend);

// ── 오차범위 바 플러그인 ───────────────────────────────────────────────────────
// 호버 시: 중앙 점 사라짐, 위아래 끝점 두 개 + 색깔 채워진 바 즉시 표시
let _activeIdx = -1;

/** pointRadius 배열: 호버 인덱스만 0으로 */
function makeRadii(len: number, hiddenIdx: number, normal: number): number[] {
  return Array.from({ length: len }, (_, i) => (i === hiddenIdx ? 0 : normal));
}

const ERROR_BAR_PLUGIN: Plugin<'line'> = {
  id: 'errorBar',

  afterEvent(chart, { event }) {
    const isLeave = event.type === 'mouseout' || event.type === 'mouseleave';
    const active = isLeave ? [] : chart.getActiveElements();
    const newIdx = active.length > 0 ? active[0].index : -1;
    if (newIdx === _activeIdx) return;

    _activeIdx = newIdx;
    const len = chart.data.datasets[0]?.data.length ?? 0;
    chart.data.datasets.forEach((ds) => {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (ds as any).pointRadius = makeRadii(len, newIdx, 3);
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (ds as any).pointHoverRadius = makeRadii(len, newIdx, 5);
    });
    chart.update('none');
  },

  afterDatasetsDraw(chart) {
    const { ctx } = chart;
    const idx = _activeIdx;
    if (idx < 0) return;

    const yScale = chart.scales.y;
    const yRange = yScale.max - yScale.min;
    const yPx = yScale.bottom - yScale.top;

    chart.data.datasets.forEach((dataset, di) => {
      const meta = chart.getDatasetMeta(di);
      if (meta.hidden) return;
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const pt = meta.data[idx] as any;
      if (!pt || dataset.data[idx] == null) return;

      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const margins: number[] | undefined = (dataset as any).errorMargins;
      const margin = margins?.[idx] ?? 2.5;
      const errorPx = (margin / yRange) * yPx;
      const barW = 5;
      const dotR = 5.5;

      const x: number = pt.x;
      const y: number = pt.y;
      const color = dataset.borderColor as string;

      ctx.save();

      // ① 세로 pill 바 (두꺼운 선 + round lineCap → capsule 모양)
      ctx.strokeStyle = color + 'aa'; // 반투명
      ctx.lineWidth = barW;
      ctx.lineCap = 'round';
      ctx.beginPath();
      ctx.moveTo(x, y - errorPx);
      ctx.lineTo(x, y + errorPx);
      ctx.stroke();

      // ② 위 끝점 도트 (흰 테두리 포함)
      ctx.fillStyle = color;
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 1.5;
      ctx.lineCap = 'butt';
      ctx.beginPath();
      ctx.arc(x, y - errorPx, dotR, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();

      // ③ 아래 끝점 도트 (흰 테두리 포함)
      ctx.beginPath();
      ctx.arc(x, y + errorPx, dotR, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();

      ctx.restore();
    });
  },
};

type PollSubView = 'all' | 'party' | 'region' | 'candidate';
type TimeFilter = 'all' | '3m' | '1m';

const SUB_TABS: { key: PollSubView; label: string }[] = [
  { key: 'all', label: '전체' },
  { key: 'party', label: '정당별' },
  { key: 'region', label: '지역별' },
  { key: 'candidate', label: '후보자별' },
];

const PARTIES = MOCK_PARTY_POLL_DATA.map((p) => ({ name: p.partyName, color: p.color }));

// ─── 통계 카드 ───────────────────────────────────────────────────────────────
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
    <div className="flex-1 min-w-0 rounded-2xl border border-gray-1 dark:border-dark-l bg-white dark:bg-dark-pb p-4 flex flex-col gap-2">
      <div className="flex items-center justify-between">
        <span className="material-symbols-outlined text-xl" style={{ color: accentColor }}>
          {icon}
        </span>
        {changeLabel && (
          <span
            className="text-[10px] font-bold px-2 py-0.5 rounded-full"
            style={{
              color: positive ? '#152484' : '#C9151E',
              backgroundColor: positive ? '#E8EDFF' : '#FFEAEA',
            }}>
            {changeLabel}
          </span>
        )}
      </div>
      <p className="text-[10px] font-semibold uppercase tracking-widest text-gray-2 dark:text-gray-2">{label}</p>
      <p className="text-3xl font-black tabular-nums text-gray-4 dark:text-white leading-none">{value}</p>
      <p className="text-[11px] text-gray-2">{sub}</p>
    </div>
  );
}

// ─── 후보자 지지율 바 ─────────────────────────────────────────────────────────
function CandidateBar({ label, pct, color, max }: { label: string; pct: number; color: string; max: number }) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-[12px] text-gray-3 dark:text-gray-1 w-[64px] shrink-0 truncate">{label}</span>
      <div className="flex-1 h-2 rounded-full bg-default-100 dark:bg-dark-b overflow-hidden">
        <div
          className="h-full rounded-full animate-bar-grow"
          style={{ width: `${(pct / max) * 100}%`, backgroundColor: color }}
        />
      </div>
      <span className="text-[12px] font-bold text-gray-4 dark:text-white tabular-nums w-10 text-right">{pct}%</span>
    </div>
  );
}

// ─── 조사기관 카드 ───────────────────────────────────────────────────────────
function AgencyPollCard({ poll }: { poll: (typeof MOCK_AGENCY_POLLS)[0] }) {
  const [expanded, setExpanded] = useState(false);
  const visibleResults = expanded ? poll.results : poll.results.slice(0, 3);
  const maxPct = Math.max(...poll.results.map((r) => r.pct));

  return (
    <div className="rounded-2xl border border-gray-1 dark:border-dark-l bg-white dark:bg-dark-pb p-4 space-y-3">
      {/* 헤더 */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <div className="w-9 h-9 rounded-lg bg-default-100 dark:bg-dark-b flex items-center justify-center shrink-0">
            <span className="text-[9px] font-black text-gray-3 dark:text-gray-1 leading-tight text-center">
              {poll.agency.slice(0, 3)}
            </span>
          </div>
          <div>
            <p className="text-[13px] font-bold text-gray-4 dark:text-white leading-tight">{poll.agency}</p>
            <p className="text-[10px] text-gray-2">{poll.client} 의뢰</p>
          </div>
        </div>
        <div className="text-right shrink-0">
          <p className="text-[10px] font-semibold text-gray-3 dark:text-gray-1">{poll.publishDate.slice(0, 7)}</p>
          <p className="text-[10px] text-gray-2">오차 {poll.marginOfError}</p>
        </div>
      </div>

      {/* 질문 */}
      <p className="text-[11px] font-semibold text-gray-3 dark:text-gray-1 bg-default-100 dark:bg-dark-b rounded-lg px-3 py-2">
        {poll.questionTitle}
      </p>

      {/* 결과 바 */}
      <div className="space-y-2">
        {visibleResults
          .filter((r) => !r.label.includes('없음') && !r.label.includes('모름') && !r.label.includes('기타'))
          .map((r) => (
            <CandidateBar key={r.label} label={r.label} pct={r.pct} color={r.color ?? '#aaa'} max={maxPct} />
          ))}
      </div>

      {/* 표본/기간 메타 + 펼치기 */}
      <div className="flex items-center justify-between pt-1">
        <span className="text-[10px] text-gray-2">
          {poll.surveyPeriod} · 표본 {poll.sampleSize.toLocaleString()}명 · {poll.method}
        </span>
        {poll.results.length > 3 && (
          <button
            type="button"
            onClick={() => setExpanded(!expanded)}
            className="text-[11px] font-semibold text-primary-3 dark:text-primary-2 flex items-center gap-0.5">
            {expanded ? '접기' : '더보기'}
            <span className="material-symbols-outlined text-[14px]">{expanded ? 'expand_less' : 'expand_more'}</span>
          </button>
        )}
      </div>
    </div>
  );
}

// ─── 여론조사 테이블 ──────────────────────────────────────────────────────────
function AgencyPollTable({ polls }: { polls: typeof MOCK_AGENCY_POLLS }) {
  return (
    <div className="rounded-2xl border border-gray-1 dark:border-dark-l bg-white dark:bg-dark-pb overflow-hidden">
      {/* 테이블 헤더 */}
      <div className="px-5 py-4 flex justify-between items-center border-b border-gray-1 dark:border-dark-l">
        <h3 className="text-[14px] font-bold text-gray-4 dark:text-white">최신 여론조사</h3>
        <button
          type="button"
          className="p-1.5 bg-default-100 dark:bg-dark-b rounded-lg hover:bg-default-200 dark:hover:bg-dark-l transition-colors">
          <span className="material-symbols-outlined text-[18px] text-gray-3 dark:text-gray-1">filter_list</span>
        </button>
      </div>

      {/* 테이블 본문 */}
      <div className="overflow-x-auto">
        <table className="w-full text-left">
          <thead>
            <tr className="bg-default-50 dark:bg-dark-b border-b border-gray-1/50 dark:border-dark-l">
              <th className="px-5 py-3 text-[10px] font-bold uppercase tracking-widest text-gray-2 whitespace-nowrap">
                조사기관
              </th>
              <th className="px-5 py-3 text-[10px] font-bold uppercase tracking-widest text-gray-2">주요 질문</th>
              <th className="px-5 py-3 text-[10px] font-bold uppercase tracking-widest text-gray-2 whitespace-nowrap">
                1위
              </th>
              <th className="px-5 py-3 text-[10px] font-bold uppercase tracking-widest text-gray-2 whitespace-nowrap">
                2위
              </th>
              <th className="px-5 py-3 text-[10px] font-bold uppercase tracking-widest text-gray-2 whitespace-nowrap">
                발표일
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-1/50 dark:divide-dark-l">
            {polls.map((poll) => {
              const meaningfulResults = poll.results.filter(
                (r) => !r.label.includes('없음') && !r.label.includes('모름') && !r.label.includes('기타'),
              );
              const sorted = [...meaningfulResults].sort((a, b) => b.pct - a.pct);
              const first = sorted[0];
              const second = sorted[1];
              const maxPct = first?.pct ?? 100;

              return (
                <tr key={poll.id} className="hover:bg-default-50 dark:hover:bg-dark-b/50 transition-colors">
                  {/* 조사기관 */}
                  <td className="px-5 py-4 whitespace-nowrap">
                    <p className="text-[12px] font-bold text-gray-4 dark:text-white leading-tight">{poll.agency}</p>
                    <p className="text-[10px] text-gray-2 mt-0.5">{poll.client} 의뢰</p>
                  </td>

                  {/* 주요 질문 */}
                  <td className="px-5 py-4 max-w-[180px] md:max-w-[240px]">
                    <p className="text-[11px] text-gray-3 dark:text-gray-1 leading-tight line-clamp-2">
                      {poll.questionTitle}
                    </p>
                    <p className="text-[10px] text-gray-2 mt-0.5">
                      n={poll.sampleSize.toLocaleString()} · {poll.marginOfError}
                    </p>
                  </td>

                  {/* 1위 */}
                  <td className="px-5 py-4 whitespace-nowrap">
                    {first ? (
                      <>
                        <div className="flex items-center gap-2">
                          <div className="w-16 bg-default-100 dark:bg-dark-b h-1.5 rounded-full overflow-hidden">
                            <div
                              className="h-full rounded-full"
                              style={{
                                width: `${(first.pct / maxPct) * 100}%`,
                                backgroundColor: first.color ?? '#aaa',
                              }}
                            />
                          </div>
                          <span className="text-[12px] font-bold text-gray-4 dark:text-white tabular-nums">
                            {first.pct}%
                          </span>
                        </div>
                        <p className="text-[10px] text-gray-2 mt-0.5 max-w-[100px] truncate">{first.label}</p>
                      </>
                    ) : (
                      <span className="text-[11px] text-gray-2">—</span>
                    )}
                  </td>

                  {/* 2위 */}
                  <td className="px-5 py-4 whitespace-nowrap">
                    {second ? (
                      <>
                        <div className="flex items-center gap-2">
                          <div className="w-16 bg-default-100 dark:bg-dark-b h-1.5 rounded-full overflow-hidden">
                            <div
                              className="h-full rounded-full"
                              style={{
                                width: `${(second.pct / maxPct) * 100}%`,
                                backgroundColor: second.color ?? '#aaa',
                              }}
                            />
                          </div>
                          <span className="text-[12px] font-bold text-gray-4 dark:text-white tabular-nums">
                            {second.pct}%
                          </span>
                        </div>
                        <p className="text-[10px] text-gray-2 mt-0.5 max-w-[100px] truncate">{second.label}</p>
                      </>
                    ) : (
                      <span className="text-[11px] text-gray-2">—</span>
                    )}
                  </td>

                  {/* 발표일 */}
                  <td className="px-5 py-4 whitespace-nowrap">
                    <p className="text-[11px] font-semibold text-gray-3 dark:text-gray-1">{poll.publishDate}</p>
                    <p className="text-[10px] text-gray-2 mt-0.5">{poll.surveyPeriod}</p>
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

// ─── 전체 뷰 ─────────────────────────────────────────────────────────────────
function OverallView() {
  const [timeFilter, setTimeFilter] = useState<TimeFilter>('all');

  const minjooData = MOCK_AGENCY_POLLS.find((p) => p.id === 'realmeter-ohmy-minjoo-2603')!;
  const pppData = MOCK_AGENCY_POLLS.find((p) => p.id === 'realmeter-ohmy-ppp-2603')!;
  const partyData = MOCK_AGENCY_POLLS.find((p) => p.id === 'realmeter-party-2603')!;

  const filteredTimeseries = (() => {
    const now = new Date('2026-03-13');
    if (timeFilter === '1m') {
      const cutoff = new Date(now);
      cutoff.setMonth(cutoff.getMonth() - 1);
      return MOCK_POLL_TIMESERIES.filter((d) => new Date(d.date) >= cutoff);
    }
    if (timeFilter === '3m') {
      const cutoff = new Date(now);
      cutoff.setMonth(cutoff.getMonth() - 3);
      return MOCK_POLL_TIMESERIES.filter((d) => new Date(d.date) >= cutoff);
    }
    return MOCK_POLL_TIMESERIES;
  })();

  const minjooMax = Math.max(...(minjooData?.results.map((r) => r.pct) ?? [1]));
  const pppMax = Math.max(...(pppData?.results.map((r) => r.pct) ?? [1]));

  return (
    <div className="space-y-5 px-4 pb-8 pt-3">
      {/* 헤더: 지역 + 기간 필터 */}
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-1.5">
          <span className="material-symbols-outlined text-[16px] text-primary-3 dark:text-primary-2">location_on</span>
          <span className="text-[13px] font-bold text-gray-4 dark:text-white">{POLL_SUMMARY.region}</span>
          <span className="text-[11px] text-gray-2">· {POLL_SUMMARY.election}</span>
        </div>
        <div className="flex bg-default-100 dark:bg-dark-b rounded-lg p-0.5 gap-0.5">
          {(
            [
              ['all', '전체'],
              ['3m', '3개월'],
              ['1m', '1개월'],
            ] as [TimeFilter, string][]
          ).map(([key, label]) => (
            <button
              type="button"
              key={key}
              onClick={() => setTimeFilter(key)}
              className={`px-2.5 py-1 rounded-md text-[11px] font-bold transition-all ${
                timeFilter === key
                  ? 'bg-white dark:bg-dark-pb text-gray-4 dark:text-white shadow-sm'
                  : 'text-gray-2 dark:text-gray-2'
              }`}>
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* ── 벤토 그리드 ─────────────────────────────────────────────────────── */}

      {/* 1행: 통계 카드 3개 (모바일: 가로 스크롤, 데스크톱: 3열) */}
      <div className="flex gap-3 overflow-x-auto pb-1 -mx-4 px-4 md:overflow-visible md:mx-0 md:px-0 md:grid md:grid-cols-3">
        <StatCard
          icon="bar_chart"
          label="1위 정당 지지율"
          value={`${POLL_SUMMARY.leadingParty.pct}%`}
          sub={`${POLL_SUMMARY.leadingParty.name} · 리얼미터 2026.03`}
          changeLabel={`${POLL_SUMMARY.leadingParty.change > 0 ? '▲' : '▼'}${Math.abs(POLL_SUMMARY.leadingParty.change)}%p`}
          positive={POLL_SUMMARY.leadingParty.change > 0}
          accentColor={POLL_SUMMARY.leadingParty.color}
        />
        <StatCard
          icon="trending_down"
          label="1·2위 지지율 격차"
          value={`${POLL_SUMMARY.gap}%p`}
          sub={`${POLL_SUMMARY.leadingParty.name} vs ${POLL_SUMMARY.runnerUpParty.name}`}
          changeLabel="압도적"
          positive
          accentColor="#555"
        />
        <StatCard
          icon="group"
          label="부동층 (없음+모름)"
          value={`${POLL_SUMMARY.undecided}%`}
          sub="지지정당 없음·잘모름 합산"
          accentColor="#999"
        />
      </div>

      {/* 2행: 추이 차트 + 정당지지율 바 */}
      <div className="md:grid md:grid-cols-5 md:gap-4 space-y-4 md:space-y-0">
        {/* 추이 차트 (모바일 전체, 데스크톱 3/5) */}
        <div className="md:col-span-3 rounded-3xl bg-white dark:bg-dark-pb shadow-sm border border-gray-1/60 dark:border-dark-l p-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-[14px] font-semibold text-gray-4 dark:text-white tracking-tight">정당지지율 추이</h3>
              <p className="text-[10px] text-gray-2 mt-0.5">{POLL_SUMMARY.source} 기준</p>
            </div>
            <div className="flex flex-wrap gap-x-3 gap-y-1.5 justify-end">
              {MOCK_PARTY_POLL_DATA.map((p) => (
                <span
                  key={p.partyName}
                  className="flex items-center gap-1.5 text-[10px] text-gray-3 dark:text-gray-1 font-medium">
                  <span className="w-5 h-1.5 rounded-full inline-block" style={{ backgroundColor: p.color }} />
                  {p.partyName
                    .replace('더불어민주', '민주')
                    .replace('국민의힘', '국힘')
                    .replace('개혁신당', '개혁')
                    .replace('조국혁신당', '조국')}
                </span>
              ))}
            </div>
          </div>
          <div className="h-[210px]">
            <Line
              plugins={[ERROR_BAR_PLUGIN]}
              data={{
                labels: filteredTimeseries.map((d) => {
                  const [, m, day] = d.date.split('-');
                  return `${+m}/${+day}`;
                }),
                datasets: MOCK_PARTY_POLL_DATA.map((p, i) => ({
                  label: p.partyName,
                  data: filteredTimeseries.map((d) => {
                    const key = p.partyName as keyof typeof d;
                    return typeof d[key] === 'number' ? (d[key] as number) : null;
                  }),
                  // 오차범위 데이터 (poll당 동일하지만 포인트별로 다를 수 있음)
                  errorMargins: filteredTimeseries.map((d) => d.marginOfError),
                  borderColor: p.color,
                  backgroundColor: 'transparent',
                  tension: 0.35,
                  pointRadius: 3,
                  pointBackgroundColor: p.color,
                  pointBorderColor: '#ffffff',
                  pointBorderWidth: 1.5,
                  pointHoverRadius: 5,
                  pointHoverBackgroundColor: p.color,
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
                  tooltip: {
                    backgroundColor: 'rgba(255,255,255,0.97)',
                    titleColor: '#0f172a',
                    bodyColor: '#64748b',
                    borderColor: 'rgba(0,0,0,0.07)',
                    borderWidth: 1,
                    cornerRadius: 14,
                    padding: { x: 12, y: 9 },
                    boxPadding: 5,
                    usePointStyle: true,
                    titleFont: { size: 11, weight: 'bold' },
                    bodyFont: { size: 11 },
                    callbacks: {
                      title: (items) => items[0]?.label ?? '',
                      label: (ctx) => {
                        const v = ctx.parsed.y;
                        return v != null ? ` ${ctx.dataset.label}: ${v}%` : '';
                      },
                    },
                  },
                },
                scales: {
                  y: {
                    min: 0,
                    max: 65,
                    grid: { display: false },
                    border: { display: false },
                    ticks: {
                      callback: (v) => `${v}%`,
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
                    border: { display: false, dash: [4, 4] },
                    ticks: {
                      font: { size: 10 },
                      color: '#94a3b8',
                      maxRotation: 0,
                      maxTicksLimit: 7,
                      padding: 6,
                    },
                  },
                },
                animation: { duration: 600, easing: 'easeInOutQuart' },
              }}
            />
          </div>
        </div>

        {/* 최신 정당지지율 바 (모바일 전체, 데스크톱 2/5) */}
        <div className="md:col-span-2 rounded-2xl border border-gray-1 dark:border-dark-l bg-white dark:bg-dark-pb p-4">
          <h3 className="text-[13px] font-bold text-gray-4 dark:text-white mb-3">현재 정당지지율</h3>
          <div className="space-y-2.5">
            {partyData.results
              .filter((r) => !r.label.includes('없음') && !r.label.includes('모름'))
              .map((r) => (
                <div key={r.label}>
                  <div className="flex justify-between text-[11px] mb-1">
                    <span className="font-medium text-gray-3 dark:text-gray-1">{r.label}</span>
                    <span className="font-bold text-gray-4 dark:text-white">{r.pct}%</span>
                  </div>
                  <div className="h-2 w-full rounded-full bg-default-100 dark:bg-dark-b overflow-hidden">
                    <div
                      className="h-full rounded-full animate-bar-grow origin-left"
                      style={{ width: `${r.pct}%`, backgroundColor: r.color ?? '#aaa' }}
                    />
                  </div>
                </div>
              ))}
          </div>
          <p className="text-[10px] text-gray-2 mt-3">
            {partyData.surveyPeriod} · 표본 {partyData.sampleSize}명
          </p>
        </div>
      </div>

      {/* 3행: 경기도지사 후보 지지율 */}
      <div className="md:grid md:grid-cols-2 md:gap-4 space-y-4 md:space-y-0">
        {/* 더불어민주당 후보 */}
        <div className="rounded-2xl border border-gray-1 dark:border-dark-l bg-white dark:bg-dark-pb p-4">
          <div className="flex items-center gap-2 mb-3">
            <span className="w-3 h-3 rounded-full inline-block" style={{ backgroundColor: '#152484' }} />
            <h3 className="text-[13px] font-bold text-gray-4 dark:text-white">더불어민주당 경기도지사 후보</h3>
          </div>
          <div className="space-y-2">
            {minjooData.results
              .filter((r) => !['기타 인물', '없음', '잘 모름', '없음/모름'].includes(r.label))
              .map((r) => (
                <CandidateBar key={r.label} label={r.label} pct={r.pct} color="#152484" max={minjooMax} />
              ))}
          </div>
          <p className="text-[10px] text-gray-2 mt-3">
            {minjooData.surveyPeriod} · {minjooData.agency} · n={minjooData.sampleSize}
          </p>
        </div>

        {/* 국민의힘 후보 */}
        <div className="rounded-2xl border border-gray-1 dark:border-dark-l bg-white dark:bg-dark-pb p-4">
          <div className="flex items-center gap-2 mb-3">
            <span className="w-3 h-3 rounded-full inline-block" style={{ backgroundColor: '#C9151E' }} />
            <h3 className="text-[13px] font-bold text-gray-4 dark:text-white">국민의힘 경기도지사 후보</h3>
          </div>
          <div className="space-y-2">
            {pppData.results
              .filter((r) => !['기타인물', '없음', '잘 모름', '없음/모름'].includes(r.label))
              .map((r) => (
                <CandidateBar key={r.label} label={r.label} pct={r.pct} color="#C9151E" max={pppMax} />
              ))}
          </div>
          <p className="text-[10px] text-gray-2 mt-3">
            {pppData.surveyPeriod} · {pppData.agency} · n={pppData.sampleSize}
          </p>
        </div>
      </div>

      {/* 4행: 최신 여론조사 테이블 */}
      <AgencyPollTable polls={MOCK_AGENCY_POLLS} />

      {/* 5행: 조사기관 카드 상세 */}
      <div className="space-y-3">
        {MOCK_AGENCY_POLLS.map((poll) => (
          <AgencyPollCard key={poll.id} poll={poll} />
        ))}
      </div>
    </div>
  );
}

// ─── 메인 컴포넌트 ────────────────────────────────────────────────────────────
interface ElectionPollViewProps {
  confirmedRegion: ConfirmedRegion | null;
}

export default function ElectionPollView({ confirmedRegion }: ElectionPollViewProps) {
  const [subView, setSubView] = useState<PollSubView>('all');
  const [selectedParty, setSelectedParty] = useState<string | null>(null);
  const [selectedRegion, setSelectedRegion] = useState<SelectedRegion | null>(
    confirmedRegion ? { regionCode: confirmedRegion.regionCode, regionName: confirmedRegion.regionName } : null,
  );

  return (
    <div className="flex flex-col">
      <SubTabBar tabs={SUB_TABS} active={subView} onChange={setSubView} />

      {subView === 'all' && <OverallView />}

      {subView === 'party' && (
        <div className="space-y-4 pb-6">
          <PartyRingSelector parties={PARTIES} selected={selectedParty} onSelect={setSelectedParty} />
          {selectedParty ? (
            <div className="px-4 space-y-3">
              {/* 선택 정당 지역별 지지율 */}
              {(() => {
                const party = MOCK_PARTY_POLL_DATA.find((p) => p.partyName === selectedParty);
                if (!party) return null;
                const entries = Object.entries(party.regionalPct).sort(([, a], [, b]) => b - a);
                return (
                  <div className="rounded-2xl border border-gray-1 dark:border-dark-l bg-white dark:bg-dark-pb p-4">
                    <h3 className="text-[13px] font-bold text-gray-4 dark:text-white mb-3">
                      {selectedParty} 지역별 지지율
                    </h3>
                    <div className="space-y-2">
                      {entries.map(([region, pct]) => (
                        <div key={region} className="flex items-center gap-2">
                          <span className="text-[11px] text-gray-3 dark:text-gray-1 w-[88px] shrink-0">{region}</span>
                          <div className="flex-1 h-2 rounded-full bg-default-100 dark:bg-dark-b overflow-hidden">
                            <div
                              className="h-full rounded-full"
                              style={{ width: `${pct}%`, backgroundColor: party.color }}
                            />
                          </div>
                          <span className="text-[11px] font-bold text-gray-4 dark:text-white tabular-nums w-10 text-right">
                            {pct}%
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                );
              })()}
            </div>
          ) : (
            <p className="text-sm text-gray-2 text-center py-8 px-4">정당을 선택해 지지율 분포를 확인하세요.</p>
          )}
        </div>
      )}

      {subView === 'region' && (
        <div className="pb-6">
          <DistrictMapPicker selected={selectedRegion} onSelect={setSelectedRegion} label="지역을 선택하세요" />
          {selectedRegion?.regionName && (
            <div className="mt-4">
              <PollRegionPanel region={selectedRegion.regionName} />
            </div>
          )}
        </div>
      )}

      {subView === 'candidate' && (
        <div className="pb-6">
          <DistrictMapPicker
            selected={selectedRegion}
            onSelect={setSelectedRegion}
            label="후보자를 볼 지역을 선택하세요"
          />
          {selectedRegion?.regionName && (
            <p className="text-sm text-gray-2 text-center py-8 px-4">
              {selectedRegion.regionName} 후보자별 지지율 추이가 준비 중입니다.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
