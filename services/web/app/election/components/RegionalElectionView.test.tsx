import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import RegionalElectionView from './RegionalElectionView';

const mockUseGetElectionOverview = vi.fn();
const mockUseGetElectionRegionPanel = vi.fn();
const mockUseGetElectionCandidates = vi.fn();

vi.mock('../apis/queries', () => ({
  useGetElectionOverview: (...args: unknown[]) => mockUseGetElectionOverview(...args),
  useGetElectionRegionPanel: (...args: unknown[]) => mockUseGetElectionRegionPanel(...args),
  useGetElectionCandidates: (...args: unknown[]) => mockUseGetElectionCandidates(...args),
}));

vi.mock('./ElectionDetailPanel', () => ({
  default: ({ fallbackCandidateName, regionName }: { fallbackCandidateName?: string; regionName?: string }) => (
    <div data-testid="election-detail-panel">{`${fallbackCandidateName ?? '후보 정보'}|${regionName ?? '지역 정보'}`}</div>
  ),
}));

const createQueryResult = <T,>(data: T) => ({
  data: { data },
  isLoading: false,
});

describe('RegionalElectionView', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('supports assembly depth drill-down with breadcrumb updates', () => {
    mockUseGetElectionOverview.mockReturnValue(
      createQueryResult({
        selected_election_id: 'assembly-2024',
        ui_template: 'REGIONAL',
        default_result_card: {
          source_election_id: 'assembly-2024',
          region_type: 'DISTRICT',
          region_code: 'seoul-jongno',
          title: '제22대 국회의원선거 결과',
        },
      }),
    );
    mockUseGetElectionRegionPanel.mockReturnValue(
      createQueryResult({
        selected_election_id: 'assembly-2024',
        depth: 'DISTRICT',
        region_code: 'seoul-jongno',
        office_type: null,
        region_name: '서울 종로구',
        result_card: {
          source_election_id: 'assembly-2024',
          region_type: 'DISTRICT',
          region_code: 'seoul-jongno',
          title: '서울 종로구 결과',
        },
      }),
    );
    mockUseGetElectionCandidates.mockReturnValue(
      createQueryResult({
        selected_election_id: 'assembly-2024',
        region_code: 'seoul-jongno',
        office_type: null,
        candidates: [
          {
            candidate_id: 'candidate-1',
            candidate_name: '후보 A',
            party_name: '정당 A',
            candidate_image_url: '',
          },
        ],
      }),
    );

    render(
      <RegionalElectionView
        electionId="assembly-2024"
        regionCode="seoul-jongno"
        regionType="DISTRICT"
        regionName="서울 종로구"
      />,
    );

    expect(screen.getByRole('button', { name: '전국' })).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /서울특별시/ }));
    expect(screen.getByRole('button', { name: '서울특별시' })).toBeInTheDocument();
    expect(screen.getByText('격전 지역 · 종로·용산·마포')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /종로구/ }));
    expect(screen.getByText('최종 depth 도달')).toBeInTheDocument();
    expect(screen.getByText(/이제 종로구 기준으로 후보군과 지난 결과를 함께 확인할 수 있습니다/)).toBeInTheDocument();
  }, 10000);

  it('toggles between actual map and hex cartogram modes', () => {
    mockUseGetElectionOverview.mockReturnValue(
      createQueryResult({
        selected_election_id: 'local-2026',
        ui_template: 'REGIONAL',
        default_result_card: {
          source_election_id: 'local-2026',
          region_type: 'COUNTY',
          region_code: 'seoul-jongno',
          title: '제9회 전국동시지방선거 결과',
        },
      }),
    );
    mockUseGetElectionRegionPanel.mockReturnValue(
      createQueryResult({
        selected_election_id: 'local-2026',
        depth: 'COUNTY',
        region_code: 'seoul-jongno',
        office_type: null,
        region_name: '서울 종로구',
        result_card: {
          source_election_id: 'local-2026',
          region_type: 'COUNTY',
          region_code: 'seoul-jongno',
          title: '서울 종로구 결과',
        },
      }),
    );
    mockUseGetElectionCandidates.mockReturnValue(
      createQueryResult({
        selected_election_id: 'local-2026',
        region_code: 'seoul-jongno',
        office_type: null,
        candidates: [
          {
            candidate_id: 'candidate-1',
            candidate_name: '후보 A',
            party_name: '정당 A',
            candidate_image_url: '',
          },
        ],
      }),
    );

    render(
      <RegionalElectionView
        electionId="local-2026"
        regionCode="seoul-jongno"
        regionType="COUNTY"
        regionName="서울 종로구"
      />,
    );

    expect(screen.getByRole('button', { name: '실제 지도' })).toHaveAttribute('aria-pressed', 'true');
    fireEvent.click(screen.getByRole('button', { name: '육각형 카토그램' }));
    expect(screen.getByRole('button', { name: '육각형 카토그램' })).toHaveAttribute('aria-pressed', 'true');
    expect(screen.getByTestId('regional-map-stage')).toHaveTextContent('육각형 카토그램');
  });

  it('syncs selected map depth with candidate list and detail panel context', () => {
    mockUseGetElectionOverview.mockReturnValue(
      createQueryResult({
        selected_election_id: 'local-2026',
        ui_template: 'REGIONAL',
        default_result_card: {
          source_election_id: 'local-2026',
          region_type: 'COUNTY',
          region_code: 'seoul-jongno',
          title: '제9회 전국동시지방선거 결과',
        },
      }),
    );
    mockUseGetElectionRegionPanel.mockImplementation((_: unknown, regionType: unknown, regionCode: unknown) =>
      createQueryResult({
        selected_election_id: 'local-2026',
        depth: regionType,
        region_code: regionCode,
        office_type: null,
        region_name: regionCode === 'seoul' ? '서울특별시' : '서울 종로구',
        result_card: {
          source_election_id: 'local-2026',
          region_type: regionType,
          region_code: regionCode,
          title: `${regionCode} 결과`,
        },
      }),
    );
    mockUseGetElectionCandidates.mockImplementation((_: unknown, regionCode: unknown) => {
      let candidates;

      if (regionCode === 'seoul') {
        candidates = [
          {
            candidate_id: 'candidate-seoul',
            candidate_name: '서울 후보',
            party_name: '정당 서울',
            candidate_image_url: '',
          },
        ];
      } else if (regionCode === 'national') {
        candidates = [];
      } else {
        candidates = [
          {
            candidate_id: 'candidate-jongno',
            candidate_name: '종로 후보',
            party_name: '정당 종로',
            candidate_image_url: '',
          },
        ];
      }

      return createQueryResult({
        selected_election_id: 'local-2026',
        region_code: regionCode,
        office_type: null,
        candidates,
      });
    });

    render(
      <RegionalElectionView
        electionId="local-2026"
        regionCode="seoul-jongno"
        regionType="COUNTY"
        regionName="서울 종로구"
      />,
    );

    expect(screen.getByRole('heading', { name: '전국 후보 목록' })).toBeInTheDocument();
    expect(screen.getByTestId('election-detail-panel')).toHaveTextContent('전국 예시 후보 A|전국');

    fireEvent.click(screen.getByRole('button', { name: /서울특별시/ }));

    expect(screen.getByRole('heading', { name: '서울특별시 후보 목록' })).toBeInTheDocument();
    expect(screen.getByText('서울 후보')).toBeInTheDocument();
    expect(screen.getByTestId('election-detail-panel')).toHaveTextContent('서울 후보|서울특별시');
  });
});
