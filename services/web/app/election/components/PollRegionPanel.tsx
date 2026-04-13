'use client';

import { ElectionPollRegionResponse } from '@/types';
import { aggregatePartySnapshots, normalizePartyName } from '../utils/partyName';

interface PollRegionPanelProps {
  response?: ElectionPollRegionResponse | null | undefined;
  region?: string;
}

function SnapshotBar({ label, percentage, color }: { label: string; percentage: number; color: string }) {
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs">
        <span className="text-gray-3 dark:text-gray-1">{label}</span>
        <span className="font-semibold text-gray-4 dark:text-white">{percentage}%</span>
      </div>
      <div className="h-2 w-full rounded-full bg-default-100 dark:bg-dark-b overflow-hidden">
        <div className="h-full rounded-full" style={{ width: `${percentage}%`, backgroundColor: color }} />
      </div>
    </div>
  );
}

function getBarColor(name: string) {
  const normalizedName = normalizePartyName(name);

  if (normalizedName.includes('더불어민주')) return '#152484';
  if (normalizedName.includes('국민의힘')) return '#C9151E';
  if (normalizedName === 'undecided') return '#999999';
  return '#5b6475';
}

export default function PollRegionPanel({ response, region }: PollRegionPanelProps) {
  const regionName = response?.region_name ?? region ?? '선택 지역';
  const normalizedPartySnapshot = aggregatePartySnapshots(response?.party_snapshot ?? []);

  if (!response) {
    return (
      <div className="space-y-3 px-4">
        <h3 className="text-sm font-semibold text-gray-4 dark:text-white">{regionName} 여론조사</h3>
        <p className="py-3 text-sm text-gray-2">해당 지역의 여론조사 결과가 없습니다.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4 px-4">
      <h3 className="text-sm font-semibold text-gray-4 dark:text-white">{regionName} 여론조사</h3>

      <div className="rounded-2xl border border-gray-1 dark:border-dark-l bg-white dark:bg-dark-pb p-4 space-y-4">
        <div className="space-y-3">
          <p className="text-[11px] font-semibold text-gray-3 dark:text-gray-1">정당 스냅샷</p>
          {normalizedPartySnapshot.length > 0 ? (
            normalizedPartySnapshot.map((item) => (
              <SnapshotBar
                key={item.party_name}
                label={item.party_name}
                percentage={item.percentage}
                color={getBarColor(item.party_name)}
              />
            ))
          ) : (
            <p className="text-sm text-gray-2">정당 스냅샷이 없습니다.</p>
          )}
        </div>

        <div className="space-y-3">
          <p className="text-[11px] font-semibold text-gray-3 dark:text-gray-1">후보 스냅샷</p>
          {response.candidate_snapshot.length > 0 ? (
            response.candidate_snapshot.map((item) => (
              <SnapshotBar
                key={item.candidate_name}
                label={item.candidate_name}
                percentage={item.percentage}
                color={getBarColor(item.candidate_name)}
              />
            ))
          ) : (
            <p className="text-sm text-gray-2">후보 스냅샷이 없습니다.</p>
          )}
        </div>

        <div className="space-y-2">
          <p className="text-[11px] font-semibold text-gray-3 dark:text-gray-1">최신 조사</p>
          {response.latest_surveys.length > 0 ? (
            response.latest_surveys.map((survey) => (
              <div
                key={survey.registration_number}
                className="flex items-center justify-between rounded-xl bg-default-50 dark:bg-dark-b px-3 py-2">
                <div>
                  <p className="text-[12px] font-semibold text-gray-4 dark:text-white">{survey.pollster}</p>
                  <p className="text-[10px] text-gray-2">{survey.registration_number}</p>
                </div>
                <p className="text-[11px] text-gray-2">{survey.survey_end_date}</p>
              </div>
            ))
          ) : (
            <p className="text-sm text-gray-2">표시할 조사가 없습니다.</p>
          )}
        </div>
      </div>
    </div>
  );
}
