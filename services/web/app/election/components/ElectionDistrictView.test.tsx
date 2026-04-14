// services/web/app/election/components/ElectionDistrictView.test.tsx
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, it, expect, vi } from 'vitest';
import ElectionDistrictView from './ElectionDistrictView';

const mockUseGetElectionCandidates = vi.fn();
const mockUseGetElectionCandidateDetails = vi.fn();
const mockUseGetElectionPollRegion = vi.fn();

vi.mock('../apis/queries', () => ({
  useGetElectionCandidates: (...args: unknown[]) => mockUseGetElectionCandidates(...args),
  useGetElectionCandidateDetails: (...args: unknown[]) => mockUseGetElectionCandidateDetails(...args),
  useGetElectionPollRegion: (...args: unknown[]) => mockUseGetElectionPollRegion(...args),
}));

vi.mock('./PollRegionPanel', () => ({
  default: ({ region, response }: { region?: string; response?: { region_name?: string } | null }) => (
    <div data-testid="poll-region-panel">{`${region ?? 'none'}|${response?.region_name ?? 'no-response'}`}</div>
  ),
}));
vi.mock('./FeedRegionPanel', () => ({
  default: ({ region }: { region: string }) => <div data-testid="feed-region-panel">{region}</div>,
}));
vi.mock('./shared/DistrictMapPicker', () => ({
  default: ({ onSelect }: { onSelect: (r: { regionCode: string; regionName: string } | null) => void }) => (
    <button type="button" onClick={() => onSelect({ regionCode: '11', regionName: '서울특별시' })}>
      지역 선택
    </button>
  ),
}));

const createQueryResult = <T,>(data: T) => ({
  data: { data },
  isLoading: false,
  isError: false,
});

const createCandidateDetailsResult = (data: unknown[]) => ({
  data,
  isLoading: false,
  isError: false,
});

describe('ElectionDistrictView', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    mockUseGetElectionCandidates.mockReturnValue(
      createQueryResult({
        selected_election_id: 'local-2026',
        region_code: '11',
        office_type: null,
        candidates: [
          {
            candidate_id: 'candidate-1',
            candidate_name: '홍길동',
            party_name: '더불어민주당',
            candidate_image_url: '',
          },
        ],
      }),
    );

    mockUseGetElectionCandidateDetails.mockReturnValue(
      createCandidateDetailsResult([
        {
          candidate_id: 'candidate-1',
          candidate_name: '홍길동',
          party_name: '더불어민주당',
          candidate_image_url: '',
          career1: '전 서울시 경제부시장',
          career2: '전 국회의원',
          manifesto_items: [
            { order: 1, title: '청년 공공임대주택 5만 호 공급', content: '상세 내용' },
            { order: 2, title: '대중교통 요금 동결', content: '상세 내용' },
          ],
        },
      ]),
    );

    mockUseGetElectionPollRegion.mockReturnValue(
      createQueryResult({
        region_name: '서울특별시',
        party_snapshot: [{ party_name: '더불어민주당', percentage: 47.3 }],
        candidate_snapshot: [{ candidate_name: '홍길동', percentage: 47.3 }],
        latest_surveys: [],
      }),
    );
  });

  it('지역구가 설정되면 지역명을 표시한다', () => {
    render(
      <ElectionDistrictView
        confirmedRegion={{ regionCode: '11', regionName: '서울특별시' }}
        selectedElectionId="local-2026"
        onRegionChange={vi.fn()}
      />,
    );
    expect(screen.getAllByText(/서울특별시/).length).toBeGreaterThan(0);
  });

  it('지역구가 없으면 설정 유도 UI를 표시한다', () => {
    render(<ElectionDistrictView confirmedRegion={null} selectedElectionId="local-2026" onRegionChange={vi.fn()} />);
    expect(screen.getByText('지역구를 설정해보세요')).toBeInTheDocument();
  });

  it('선택된 선거와 지역으로 후보 및 여론 실데이터를 조회한다', () => {
    render(
      <ElectionDistrictView
        confirmedRegion={{ regionCode: '11', regionName: '서울특별시' }}
        selectedElectionId="local-2026"
        onRegionChange={vi.fn()}
      />,
    );

    expect(mockUseGetElectionCandidates).toHaveBeenCalledWith('local-2026', '11', undefined);
    expect(mockUseGetElectionCandidateDetails).toHaveBeenCalledWith('local-2026', ['candidate-1'], true);
    expect(mockUseGetElectionPollRegion).toHaveBeenCalledWith('local-2026', '11', true);
  });

  it('후보 카드와 지역 여론 패널에 실데이터 응답을 반영한다', () => {
    mockUseGetElectionCandidates.mockReturnValue(
      createQueryResult({
        selected_election_id: 'local-2026',
        region_code: '11',
        office_type: null,
        candidates: [
          {
            candidate_id: 'candidate-1',
            candidate_name: '김실데이터',
            party_name: '더불어민주당',
            candidate_image_url: '',
          },
          {
            candidate_id: 'candidate-2',
            candidate_name: '이실데이터',
            party_name: '국민의힘',
            candidate_image_url: '',
          },
        ],
      }),
    );

    mockUseGetElectionCandidateDetails.mockReturnValue(
      createCandidateDetailsResult([
        {
          candidate_id: 'candidate-1',
          candidate_name: '김실데이터',
          party_name: '더불어민주당',
          candidate_image_url: '',
          career1: '전 서울특별시 부시장',
          career2: '전 기획재정부 차관',
          manifesto_items: [
            { order: 1, title: '광역철도 연장', content: '상세 내용' },
            { order: 2, title: '청년주택 공급', content: '상세 내용' },
          ],
        },
        {
          candidate_id: 'candidate-2',
          candidate_name: '이실데이터',
          party_name: '국민의힘',
          candidate_image_url: '',
          career1: '전 행정안전부 장관',
          career2: '전 서울시 부시장',
          manifesto_items: [
            { order: 1, title: '교통체증 해소', content: '상세 내용' },
            { order: 2, title: '안전도시 구축', content: '상세 내용' },
          ],
        },
      ]),
    );

    mockUseGetElectionPollRegion.mockReturnValue(
      createQueryResult({
        region_name: '서울특별시',
        party_snapshot: [
          { party_name: '더불어민주당', percentage: 37.5 },
          { party_name: '국민의힘', percentage: 35.1 },
        ],
        candidate_snapshot: [
          { candidate_name: '김실데이터', percentage: 37.5 },
          { candidate_name: '이실데이터', percentage: 35.1 },
        ],
        latest_surveys: [],
      }),
    );

    render(
      <ElectionDistrictView
        confirmedRegion={{ regionCode: '11', regionName: '서울특별시' }}
        selectedElectionId="local-2026"
        onRegionChange={vi.fn()}
      />,
    );

    expect(screen.getByText('김실데이터')).toBeInTheDocument();
    expect(screen.getByText('이실데이터')).toBeInTheDocument();
    expect(screen.getAllByText('37.5%').length).toBeGreaterThan(0);
    expect(screen.getByText('광역철도 연장')).toBeInTheDocument();
    expect(screen.getByTestId('poll-region-panel')).toHaveTextContent('서울특별시|서울특별시');
    expect(screen.queryByText('홍길동')).not.toBeInTheDocument();
  });

  it('PollRegionPanel과 FeedRegionPanel이 렌더링된다', () => {
    render(
      <ElectionDistrictView
        confirmedRegion={{ regionCode: '11', regionName: '서울특별시' }}
        selectedElectionId="local-2026"
        onRegionChange={vi.fn()}
      />,
    );
    expect(screen.getByTestId('poll-region-panel')).toBeInTheDocument();
    expect(screen.getByTestId('feed-region-panel')).toBeInTheDocument();
  });
});
