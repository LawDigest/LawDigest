import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import PresidentialElectionView from './PresidentialElectionView';

const mockUseGetElectionOverview = vi.fn();
const mockUseGetElectionCandidates = vi.fn();
const mockUseGetElectionMap = vi.fn();
const mockUseGetElectionRegionPanel = vi.fn();

vi.mock('../apis/queries', () => ({
  useGetElectionOverview: (...args: unknown[]) => mockUseGetElectionOverview(...args),
  useGetElectionCandidates: (...args: unknown[]) => mockUseGetElectionCandidates(...args),
  useGetElectionMap: (...args: unknown[]) => mockUseGetElectionMap(...args),
  useGetElectionRegionPanel: (...args: unknown[]) => mockUseGetElectionRegionPanel(...args),
}));

vi.mock('./ElectionDetailPanel', () => ({
  default: ({ fallbackCandidateName, regionName }: { fallbackCandidateName?: string; regionName?: string }) => (
    <div data-testid="president-detail">{`${fallbackCandidateName ?? '후보 정보'}|${regionName ?? '지역 정보'}`}</div>
  ),
}));

const createQueryResult = <T,>(data: T) => ({
  data: { data },
  isLoading: false,
});

describe('PresidentialElectionView', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('switches between candidate and regional result views', async () => {
    mockUseGetElectionOverview.mockReturnValue(
      createQueryResult({
        selected_election_id: 'president-2027',
        ui_template: 'CANDIDATE',
        default_result_card: {
          source_election_id: 'president-2027',
          region_type: 'NATIONAL',
          region_code: 'national',
          title: '제21대 대통령선거 개요',
        },
      }),
    );
    mockUseGetElectionCandidates.mockReturnValue(
      createQueryResult({
        selected_election_id: 'president-2027',
        region_code: 'national',
        office_type: null,
        candidates: [
          {
            candidate_id: 'candidate-a',
            candidate_name: '후보 A',
            party_name: '정당 A',
            candidate_image_url: '',
          },
          {
            candidate_id: 'candidate-b',
            candidate_name: '후보 B',
            party_name: '정당 B',
            candidate_image_url: '',
          },
        ],
      }),
    );
    mockUseGetElectionMap.mockReturnValue(
      createQueryResult({
        selected_election_id: 'president-2027',
        depth: 'PROVINCE',
        region_code: 'national',
        view_mode: 'RESULT',
        regions: [
          { region_code: 'seoul', region_name: '서울특별시', value: '후보 A 52.1%' },
          { region_code: 'busan', region_name: '부산광역시', value: '후보 B 54.8%' },
        ],
      }),
    );
    mockUseGetElectionRegionPanel.mockImplementation((_: unknown, __: unknown, regionCode: unknown) => {
      if (regionCode === 'busan') {
        return createQueryResult({
          selected_election_id: 'president-2027',
          depth: 'PROVINCE',
          region_code: 'busan',
          office_type: null,
          region_name: '부산광역시',
          result_card: {
            source_election_id: 'president-2027',
            region_type: 'PROVINCE',
            region_code: 'busan',
            title: '부산광역시 결과',
          },
        });
      }

      return createQueryResult({
        selected_election_id: 'president-2027',
        depth: 'PROVINCE',
        region_code: 'seoul',
        office_type: null,
        region_name: '서울특별시',
        result_card: {
          source_election_id: 'president-2027',
          region_type: 'PROVINCE',
          region_code: 'seoul',
          title: '서울특별시 결과',
        },
      });
    });

    render(<PresidentialElectionView electionId="president-2027" />);

    expect(screen.getByRole('button', { name: '후보자 보기' })).toHaveAttribute('aria-pressed', 'true');
    expect(screen.getByText('후보 A')).toBeInTheDocument();
    expect(screen.getByTestId('president-detail')).toHaveTextContent('후보 A|전국');

    fireEvent.click(screen.getByRole('button', { name: /후보 B 정당 B/ }));

    await waitFor(() => {
      expect(screen.getByTestId('president-detail')).toHaveTextContent('후보 B|전국');
    });

    fireEvent.click(screen.getByRole('button', { name: '지역 결과 보기' }));

    expect(screen.getByRole('button', { name: '지역 결과 보기' })).toHaveAttribute('aria-pressed', 'true');
    expect(screen.getAllByText('서울특별시 결과').length).toBeGreaterThan(0);
    expect(screen.getAllByText('서울특별시').length).toBeGreaterThan(0);
    expect(screen.getAllByText('부산광역시').length).toBeGreaterThan(0);

    fireEvent.click(screen.getByRole('button', { name: /부산광역시 후보 B 54.8%/ }));

    await waitFor(() => {
      expect(screen.getAllByText('부산광역시 결과').length).toBeGreaterThan(0);
    });
  });
});
