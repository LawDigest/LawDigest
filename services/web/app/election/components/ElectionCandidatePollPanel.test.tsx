import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import ElectionCandidatePollPanel from './ElectionCandidatePollPanel';

vi.mock('react-chartjs-2', () => ({
  Line: ({ data }: { data: { labels: string[] } }) => <div data-testid="line-chart">{data.labels?.join(',')}</div>,
}));

describe('ElectionCandidatePollPanel', () => {
  it('기준 질문과 후보 옵션을 렌더링한다', () => {
    const onSelectCandidate = vi.fn();

    render(
      <ElectionCandidatePollPanel
        onSelectCandidate={onSelectCandidate}
        response={{
          selected_candidate: '김동연',
          basis_question_kind: 'MATCHUP',
          candidate_options: ['김동연', '양향자'],
          series: [
            {
              survey: { registration_number: '서울-002', pollster: '한국리서치', survey_end_date: '2026-04-02' },
              percentage: 45.1,
            },
          ],
          comparison_series: [],
          latest_snapshot: [{ candidate_name: '김동연', percentage: 45.1 }],
        }}
      />,
    );

    expect(screen.getByText('기준 질문: MATCHUP')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '김동연' })).toBeInTheDocument();
    expect(screen.getByTestId('line-chart')).toBeInTheDocument();
  });

  it('후보 버튼 클릭 시 선택 콜백을 호출한다', () => {
    const onSelectCandidate = vi.fn();

    render(
      <ElectionCandidatePollPanel
        onSelectCandidate={onSelectCandidate}
        response={{
          selected_candidate: '김동연',
          basis_question_kind: 'CANDIDATE_FIT',
          candidate_options: ['김동연', '김후보'],
          series: [],
          comparison_series: [],
          latest_snapshot: [],
        }}
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: '김후보' }));
    expect(onSelectCandidate).toHaveBeenCalledWith('김후보');
  });
});
