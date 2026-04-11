'use client';

import { ElectionPollCandidateResponse } from '@/types';
import { Line } from 'react-chartjs-2';

interface ElectionCandidatePollPanelProps {
  response: ElectionPollCandidateResponse | null | undefined;
  onSelectCandidate: (candidateName: string) => void;
}

function CandidateBar({ label, percentage, color }: { label: string; percentage: number; color: string }) {
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

function palette(index: number) {
  const colors = ['#152484', '#C9151E', '#2E8B57', '#FF7210', '#6A3FA0'];
  return colors[index % colors.length];
}

export default function ElectionCandidatePollPanel({ response, onSelectCandidate }: ElectionCandidatePollPanelProps) {
  if (!response) {
    return <p className="px-4 py-6 text-sm text-gray-2">후보자별 여론조사 데이터가 없습니다.</p>;
  }

  const labels = response.series.map((item) => item.survey.survey_end_date);
  const datasets = [
    {
      label: response.selected_candidate ?? '후보',
      data: response.series.map((item) => item.percentage),
      borderColor: palette(0),
      backgroundColor: 'transparent',
      tension: 0.35,
    },
    ...response.comparison_series.map((series, index) => ({
      label: series.candidate_name,
      data: series.series.map((item) => item.percentage),
      borderColor: palette(index + 1),
      backgroundColor: 'transparent',
      tension: 0.35,
    })),
  ];

  return (
    <div className="space-y-4 px-4">
      <div className="flex flex-wrap gap-2">
        {response.candidate_options.map((candidate) => (
          <button
            key={candidate}
            type="button"
            onClick={() => onSelectCandidate(candidate)}
            className={`rounded-full px-3 py-1.5 text-xs font-semibold ${
              candidate === response.selected_candidate
                ? 'bg-gray-4 text-white dark:bg-white dark:text-gray-4'
                : 'bg-default-100 text-gray-3 dark:bg-dark-b dark:text-gray-1'
            }`}>
            {candidate}
          </button>
        ))}
      </div>

      <div className="rounded-2xl border border-gray-1 dark:border-dark-l bg-white dark:bg-dark-pb p-4 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-[13px] font-bold text-gray-4 dark:text-white">
              {response.selected_candidate ?? '후보자'} 추이
            </h3>
            <p className="text-[10px] text-gray-2">기준 질문: {response.basis_question_kind ?? '없음'}</p>
          </div>
        </div>

        <div className="h-[220px]">
          <Line
            data={{ labels, datasets }}
            options={{ responsive: true, maintainAspectRatio: false, plugins: { legend: { display: true } } }}
          />
        </div>

        <div className="space-y-3">
          {response.latest_snapshot.map((item, index) => (
            <CandidateBar
              key={item.candidate_name}
              label={item.candidate_name}
              percentage={item.percentage}
              color={palette(index)}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
