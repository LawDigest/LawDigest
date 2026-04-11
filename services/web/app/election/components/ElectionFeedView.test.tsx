// services/web/app/election/components/ElectionFeedView.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import ElectionFeedView from './ElectionFeedView';

vi.mock('../apis/queries', () => ({
  useGetElectionPollOverview: () => ({
    data: {
      data: {
        latest_surveys: [
          {
            registration_number: '서울-002',
            pollster: '한국리서치',
            survey_end_date: '2026-04-02',
            snapshot: [
              { party_name: '더불어민주당', percentage: 42.5 },
              { party_name: '국민의힘', percentage: 36.2 },
            ],
          },
        ],
      },
    },
  }),
}));

vi.mock('./feed', () => ({
  ActiveFilterBadge: ({ label, onClear }: { label: string; onClear: () => void }) => (
    <div>
      <span>{label} 필터 적용 중</span>
      <button type="button" onClick={onClear}>
        해제
      </button>
    </div>
  ),
}));

vi.mock('./shared/SubTabBar', () => ({
  default: ({
    tabs,
    active,
    onChange,
  }: {
    tabs: { key: string; label: string }[];
    active: string;
    onChange: (key: string) => void;
  }) => (
    <div role="tablist">
      {tabs.map((t) => (
        <button key={t.key} role="tab" aria-selected={active === t.key} type="button" onClick={() => onChange(t.key)}>
          {t.label}
        </button>
      ))}
    </div>
  ),
}));

vi.mock('./shared/PartyRingSelector', () => ({
  default: ({ parties, onSelect }: { parties: { name: string }[]; onSelect: (n: string) => void }) => (
    <div>
      {parties.map((p) => (
        <button key={p.name} type="button" onClick={() => onSelect(p.name)}>
          {p.name}
        </button>
      ))}
    </div>
  ),
}));

vi.mock('./shared/DistrictMapPicker', () => ({
  default: () => <div data-testid="district-map-picker">지역 선택기</div>,
}));

vi.mock('./ElectionFeedCardList', () => ({
  default: ({ items }: { items: unknown[] }) => <div data-testid="feed-card-list">카드 수: {items.length}</div>,
}));

describe('ElectionFeedView', () => {
  it('서브 뷰 탭을 렌더링한다', () => {
    render(
      <ElectionFeedView
        confirmedRegion={{ regionCode: '11', regionName: '서울특별시' }}
        selectedElectionId="local-2026"
      />,
    );
    expect(screen.getByText('전체')).toBeInTheDocument();
    expect(screen.getByText('정당별')).toBeInTheDocument();
    expect(screen.getByText('후보자별')).toBeInTheDocument();
    expect(screen.getByText('지역별')).toBeInTheDocument();
  });

  it('기본 뷰는 "전체" 탭이다', () => {
    render(<ElectionFeedView confirmedRegion={null} selectedElectionId="local-2026" />);
    const allTab = screen.getByRole('tab', { name: '전체' });
    expect(allTab).toHaveAttribute('aria-selected', 'true');
  });

  it('피드 카드 리스트가 렌더링된다', () => {
    render(<ElectionFeedView confirmedRegion={null} selectedElectionId="local-2026" />);
    expect(screen.getByTestId('feed-card-list')).toBeInTheDocument();
  });

  it('"정당별" 탭 클릭 시 PartyRingSelector가 나타난다', () => {
    render(<ElectionFeedView confirmedRegion={null} selectedElectionId="local-2026" />);
    fireEvent.click(screen.getByRole('tab', { name: '정당별' }));
    expect(screen.getByText('더불어민주당')).toBeInTheDocument();
  });
});

describe('ElectionFeedView — ActiveFilterBadge', () => {
  it('초기 상태에서는 필터 배지가 표시되지 않는다', () => {
    render(<ElectionFeedView confirmedRegion={null} selectedElectionId="local-2026" />);
    expect(screen.queryByText(/필터 적용 중/)).not.toBeInTheDocument();
  });

  it('정당을 선택하면 필터 배지가 나타난다', () => {
    render(<ElectionFeedView confirmedRegion={null} selectedElectionId="local-2026" />);
    fireEvent.click(screen.getByRole('tab', { name: '정당별' }));
    fireEvent.click(screen.getByText('더불어민주당'));
    expect(screen.getByText('더불어민주당 필터 적용 중')).toBeInTheDocument();
  });

  it('필터 배지 해제 버튼 클릭 시 배지가 사라진다', () => {
    render(<ElectionFeedView confirmedRegion={null} selectedElectionId="local-2026" />);
    fireEvent.click(screen.getByRole('tab', { name: '정당별' }));
    fireEvent.click(screen.getByText('더불어민주당'));
    fireEvent.click(screen.getByText('해제'));
    expect(screen.queryByText(/필터 적용 중/)).not.toBeInTheDocument();
  });
});
