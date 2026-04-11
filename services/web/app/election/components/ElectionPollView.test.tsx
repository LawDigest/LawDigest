import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import ElectionPollView from './ElectionPollView';

vi.mock('react-chartjs-2', () => ({
  Line: ({ data }: { data: { labels: string[] } }) => <div data-testid="line-chart">{data.labels?.join(',')}</div>,
}));

vi.mock('../apis/queries', () => ({
  useGetElectionPollOverview: () => ({
    data: {
      data: {
        leading_party: {
          party_name: '더불어민주당',
          percentage: 42.5,
          runner_up_party: '국민의힘',
          gap: 6.3,
          undecided: 15.6,
        },
        party_trend: [
          {
            survey: { registration_number: '서울-001', pollster: '한국갤럽', survey_end_date: '2026-03-26' },
            snapshot: [
              { party_name: '더불어민주당', percentage: 38 },
              { party_name: '국민의힘', percentage: 34 },
            ],
          },
        ],
        latest_surveys: [
          {
            registration_number: '서울-002',
            pollster: '한국리서치',
            sponsor: '경인일보',
            survey_end_date: '2026-04-02',
            sample_size: 1000,
            margin_of_error: '95% 신뢰수준 ±3.1%p',
            question_title: '정당지지도',
            snapshot: [
              { party_name: '더불어민주당', percentage: 42.5 },
              { party_name: '국민의힘', percentage: 36.2 },
            ],
          },
        ],
      },
    },
  }),
  useGetElectionPollParty: () => ({
    data: {
      data: {
        selected_party: '더불어민주당',
        trend_series: [
          {
            survey: { registration_number: '서울-002', pollster: '한국리서치', survey_end_date: '2026-04-02' },
            percentage: 42.5,
          },
        ],
        regional_distribution: [{ region_name: '서울특별시 전체', percentage: 42.5 }],
      },
    },
  }),
  useGetElectionPollRegion: () => ({
    data: {
      data: {
        region_name: '서울특별시 전체',
        party_snapshot: [{ party_name: '더불어민주당', percentage: 42.5 }],
        candidate_snapshot: [{ candidate_name: '김동연', percentage: 45.1 }],
        latest_surveys: [{ registration_number: '서울-002', pollster: '한국리서치', survey_end_date: '2026-04-02' }],
      },
    },
  }),
  useGetElectionPollCandidate: () => ({
    data: {
      data: {
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
      },
    },
  }),
}));

vi.mock('./shared/PartyRingSelector', () => ({
  default: ({ parties }: { parties: { name: string }[] }) => (
    <div data-testid="party-selector">{parties.map((p) => p.name).join(',')}</div>
  ),
}));

vi.mock('./shared/DistrictMapPicker', () => ({
  default: () => <div data-testid="district-picker">지역 선택기</div>,
}));

vi.mock('./shared/SubTabBar', () => ({
  default: ({
    tabs,
    active,
    onChange,
  }: {
    tabs: { key: string; label: string }[];
    active: string;
    onChange: (key: 'all' | 'party' | 'region' | 'candidate') => void;
  }) => (
    <div>
      {tabs.map((tab) => (
        <button
          key={tab.key}
          type="button"
          role="tab"
          aria-selected={active === tab.key}
          onClick={() => onChange(tab.key as 'all' | 'party' | 'region' | 'candidate')}>
          {tab.label}
        </button>
      ))}
    </div>
  ),
}));

vi.mock('./PollRegionPanel', () => ({
  default: () => <div data-testid="poll-region-panel">region-panel</div>,
}));

vi.mock('./ElectionCandidatePollPanel', () => ({
  default: () => <div data-testid="candidate-poll-panel">candidate-panel</div>,
}));

describe('ElectionPollView', () => {
  it('서브 뷰 탭 4개를 렌더링한다', () => {
    render(
      <ElectionPollView
        confirmedRegion={{ regionCode: '11', regionName: '서울특별시' }}
        selectedElectionId="local-2026"
      />,
    );
    expect(screen.getByRole('tab', { name: '전체' })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: '정당별' })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: '지역별' })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: '후보자별' })).toBeInTheDocument();
  });

  it('전체 뷰에서 실데이터 기반 라인 차트와 선두 정당을 렌더링한다', () => {
    render(
      <ElectionPollView
        confirmedRegion={{ regionCode: '11', regionName: '서울특별시' }}
        selectedElectionId="local-2026"
      />,
    );
    expect(screen.getByTestId('line-chart')).toBeInTheDocument();
    expect(screen.getAllByText('더불어민주당').length).toBeGreaterThan(0);
  });

  it('"정당별" 탭 클릭 시 PartyRingSelector가 나타난다', () => {
    render(
      <ElectionPollView
        confirmedRegion={{ regionCode: '11', regionName: '서울특별시' }}
        selectedElectionId="local-2026"
      />,
    );
    fireEvent.click(screen.getByRole('tab', { name: '정당별' }));
    expect(screen.getByTestId('party-selector')).toBeInTheDocument();
  });
});
