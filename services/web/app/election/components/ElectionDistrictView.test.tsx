// services/web/app/election/components/ElectionDistrictView.test.tsx
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import ElectionDistrictView from './ElectionDistrictView';

vi.mock('./PollRegionPanel', () => ({
  default: ({ region }: { region: string }) => <div data-testid="poll-region-panel">{region}</div>,
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

describe('ElectionDistrictView', () => {
  it('지역구가 설정되면 지역명을 표시한다', () => {
    render(
      <ElectionDistrictView
        confirmedRegion={{ regionCode: '11', regionName: '서울특별시' }}
        onRegionChange={vi.fn()}
      />,
    );
    expect(screen.getAllByText(/서울특별시/).length).toBeGreaterThan(0);
  });

  it('지역구가 없으면 설정 유도 UI를 표시한다', () => {
    render(<ElectionDistrictView confirmedRegion={null} onRegionChange={vi.fn()} />);
    expect(screen.getByText('내 지역구를 설정해보세요')).toBeInTheDocument();
  });

  it('후보자 카드가 렌더링된다', () => {
    render(
      <ElectionDistrictView
        confirmedRegion={{ regionCode: '11', regionName: '서울특별시' }}
        onRegionChange={vi.fn()}
      />,
    );
    expect(screen.getByText('홍길동')).toBeInTheDocument();
  });

  it('PollRegionPanel과 FeedRegionPanel이 렌더링된다', () => {
    render(
      <ElectionDistrictView
        confirmedRegion={{ regionCode: '11', regionName: '서울특별시' }}
        onRegionChange={vi.fn()}
      />,
    );
    expect(screen.getByTestId('poll-region-panel')).toBeInTheDocument();
    expect(screen.getByTestId('feed-region-panel')).toBeInTheDocument();
  });
});
