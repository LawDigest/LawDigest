// services/web/app/election/components/ElectionFeedView.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import ElectionFeedView from './ElectionFeedView';

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
    render(<ElectionFeedView confirmedRegion={{ regionCode: '11', regionName: '서울특별시' }} />);
    expect(screen.getByText('전체')).toBeInTheDocument();
    expect(screen.getByText('정당별')).toBeInTheDocument();
    expect(screen.getByText('후보자별')).toBeInTheDocument();
    expect(screen.getByText('지역별')).toBeInTheDocument();
  });

  it('기본 뷰는 "전체" 탭이다', () => {
    render(<ElectionFeedView confirmedRegion={null} />);
    const allTab = screen.getByRole('tab', { name: '전체' });
    expect(allTab).toHaveAttribute('aria-selected', 'true');
  });

  it('피드 카드 리스트가 렌더링된다', () => {
    render(<ElectionFeedView confirmedRegion={null} />);
    expect(screen.getByTestId('feed-card-list')).toBeInTheDocument();
  });

  it('"정당별" 탭 클릭 시 PartyRingSelector가 나타난다', () => {
    render(<ElectionFeedView confirmedRegion={null} />);
    fireEvent.click(screen.getByRole('tab', { name: '정당별' }));
    expect(screen.getByText('더불어민주당')).toBeInTheDocument();
  });
});
