// services/web/app/election/components/ElectionPollView.tsx

'use client';

import { useState } from 'react';
import { Bar, Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { ConfirmedRegion } from './ElectionMapShell';
import { MOCK_POLL_DATA } from '../data/mockPollData';
import { MOCK_PARTY_POLL_DATA } from '../data/mockPartyPollData';
import { MOCK_POLL_TIMESERIES, PollTimeseriesPoint } from '../data/mockPollTimeseriesData';
import PartyRingSelector from './shared/PartyRingSelector';
import DistrictMapPicker, { SelectedRegion } from './shared/DistrictMapPicker';
import PollRegionPanel from './PollRegionPanel';

ChartJS.register(CategoryScale, LinearScale, BarElement, LineElement, PointElement, Title, Tooltip, Legend);

type PollSubView = 'all' | 'party' | 'region' | 'candidate';

const SUB_TABS: { key: PollSubView; label: string }[] = [
  { key: 'all', label: '전체' },
  { key: 'party', label: '정당별' },
  { key: 'region', label: '지역별' },
  { key: 'candidate', label: '후보자별' },
];

const PARTIES = MOCK_PARTY_POLL_DATA.map((p) => ({ name: p.partyName, color: p.color }));

// PollTimeseriesPoint에서 정당명에 해당하는 값을 안전하게 추출
const TIMESERIES_PARTY_KEYS: (keyof PollTimeseriesPoint)[] = ['더불어민주당', '국민의힘', '조국혁신당'];

interface ElectionPollViewProps {
  confirmedRegion: ConfirmedRegion | null;
}

function OverallView() {
  const barData = {
    labels: MOCK_PARTY_POLL_DATA.map((p) => p.partyName),
    datasets: [
      {
        label: '전국 지지율',
        data: MOCK_PARTY_POLL_DATA.map((p) => p.nationalPct),
        backgroundColor: MOCK_PARTY_POLL_DATA.map((p) => p.color),
        borderRadius: 6,
      },
    ],
  };

  const lineData = {
    labels: MOCK_POLL_TIMESERIES.map((d) => d.date.slice(5)),
    datasets: MOCK_PARTY_POLL_DATA.map((p) => {
      const key = p.partyName as keyof PollTimeseriesPoint;
      const isValidKey = TIMESERIES_PARTY_KEYS.includes(key);
      return {
        label: p.partyName,
        data: MOCK_POLL_TIMESERIES.map((d) => (isValidKey ? (d[key] as number) : 0)),
        borderColor: p.color,
        backgroundColor: `${p.color}22`,
        tension: 0.4,
        pointRadius: 3,
      };
    }),
  };

  const chartOptions = { responsive: true, plugins: { legend: { display: false } } };

  return (
    <div className="space-y-6 px-4 pb-6 pt-3">
      <div>
        <h3 className="text-sm font-semibold text-gray-4 dark:text-white mb-3">정당별 지지율</h3>
        <Bar data={barData} options={{ ...chartOptions, indexAxis: 'y' as const }} />
      </div>
      {/* TODO: 지역별 우세 정당 히트맵 — KoreaMap에 히트맵 모드 prop 추가 후 구현 (기능 구현 단계) */}
      <div>
        <h3 className="text-sm font-semibold text-gray-4 dark:text-white mb-3">지지율 추이 (최근 30일)</h3>
        <div className="flex gap-3 mb-2 flex-wrap">
          {MOCK_PARTY_POLL_DATA.map((p) => (
            <span key={p.partyName} className="flex items-center gap-1 text-[11px] text-gray-3 dark:text-gray-1">
              <span className="inline-block w-2.5 h-2.5 rounded-full" style={{ backgroundColor: p.color }} />
              {p.partyName}
            </span>
          ))}
        </div>
        <Line data={lineData} options={chartOptions} />
      </div>
      <div>
        <h3 className="text-sm font-semibold text-gray-4 dark:text-white mb-3">최신 여론조사</h3>
        {Object.entries(MOCK_POLL_DATA)
          .slice(0, 5)
          .map(([region, result]) => (
            <div
              key={region}
              className="rounded-xl border border-gray-1 dark:border-dark-l bg-white dark:bg-dark-pb p-3 mb-2">
              <div className="flex justify-between items-center mb-2">
                <span className="text-xs font-medium text-gray-3 dark:text-gray-1">{region}</span>
                <span className="text-[10px] text-gray-2">{result.source}</span>
              </div>
              {[
                { name: '더불어민주당', pct: result.c1Pct },
                { name: '국민의힘', pct: result.c2Pct },
              ].map((r) => (
                <div key={r.name} className="flex items-center gap-2 mb-1">
                  <span className="text-[11px] text-gray-3 dark:text-gray-1 w-[80px] shrink-0">{r.name}</span>
                  <div className="flex-1 h-1.5 rounded-full bg-default-100 dark:bg-dark-b overflow-hidden">
                    <div className="h-full rounded-full bg-primary-2" style={{ width: `${r.pct}%` }} />
                  </div>
                  <span className="text-[11px] font-semibold text-gray-4 dark:text-white">{r.pct}%</span>
                </div>
              ))}
            </div>
          ))}
      </div>
    </div>
  );
}

export default function ElectionPollView({ confirmedRegion }: ElectionPollViewProps) {
  const [subView, setSubView] = useState<PollSubView>('all');
  const [selectedParty, setSelectedParty] = useState<string | null>(null);
  const [selectedRegion, setSelectedRegion] = useState<SelectedRegion | null>(
    confirmedRegion ? { regionCode: confirmedRegion.regionCode, regionName: confirmedRegion.regionName } : null,
  );

  return (
    <div className="flex flex-col">
      {/* 서브 뷰 탭 */}
      <nav className="flex border-b border-gray-1 dark:border-dark-l overflow-x-auto scrollbar-hide">
        {SUB_TABS.map(({ key, label }) => {
          const isActive = key === subView;
          return (
            <button
              key={key}
              type="button"
              role="tab"
              aria-selected={isActive}
              onClick={() => setSubView(key)}
              className={[
                'relative flex-1 min-w-[72px] py-2.5 text-sm font-semibold transition-colors whitespace-nowrap',
                isActive ? 'text-gray-4 dark:text-white' : 'text-gray-2 hover:text-gray-3',
              ].join(' ')}>
              {label}
              {isActive && (
                <span className="absolute bottom-0 left-1/2 -translate-x-1/2 h-[3px] w-6 rounded-full bg-gradient-to-r from-primary-2 to-primary-3" />
              )}
            </button>
          );
        })}
      </nav>

      {subView === 'all' && <OverallView />}

      {subView === 'party' && (
        <div className="space-y-4 pb-6">
          <PartyRingSelector parties={PARTIES} selected={selectedParty} onSelect={setSelectedParty} />
          {selectedParty ? (
            <div className="px-4">
              <p className="text-sm text-gray-2 text-center py-8">
                {selectedParty} 지지율 상세 데이터가 준비 중입니다.
              </p>
            </div>
          ) : (
            <p className="text-sm text-gray-2 text-center py-8 px-4">정당을 선택해 지지율 추이를 확인하세요.</p>
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
