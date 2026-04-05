// services/web/app/election/components/ElectionPollView.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import ElectionPollView from './ElectionPollView';

// Chart.js는 Canvas API가 없는 jsdom에서 동작하지 않으므로 모킹
vi.mock('react-chartjs-2', () => ({
  Bar: ({ data }: { data: { labels: string[] } }) => <div data-testid="bar-chart">{data.labels?.join(',')}</div>,
  Line: ({ data }: { data: { labels: string[] } }) => <div data-testid="line-chart">{data.labels?.join(',')}</div>,
}));

vi.mock('./shared/PartyRingSelector', () => ({
  default: ({ parties }: { parties: { name: string }[] }) => (
    <div>
      {parties.map((p) => (
        <span key={p.name}>{p.name}</span>
      ))}
    </div>
  ),
}));

vi.mock('./shared/DistrictMapPicker', () => ({
  default: () => <div data-testid="district-picker">지역 선택기</div>,
}));

vi.mock('./PollRegionPanel', () => ({
  default: ({ region }: { region: string }) => <div data-testid="poll-region-panel">{region}</div>,
}));

describe('ElectionPollView', () => {
  it('서브 뷰 탭 4개를 렌더링한다', () => {
    render(<ElectionPollView confirmedRegion={{ regionCode: '11', regionName: '서울특별시' }} />);
    expect(screen.getByRole('tab', { name: '전체' })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: '정당별' })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: '지역별' })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: '후보자별' })).toBeInTheDocument();
  });

  it('전체 뷰에서 바차트가 렌더링된다', () => {
    render(<ElectionPollView confirmedRegion={null} />);
    expect(screen.getByTestId('bar-chart')).toBeInTheDocument();
  });

  it('"정당별" 탭 클릭 시 PartyRingSelector가 나타난다', () => {
    render(<ElectionPollView confirmedRegion={null} />);
    fireEvent.click(screen.getByRole('tab', { name: '정당별' }));
    expect(screen.getByText('더불어민주당')).toBeInTheDocument();
  });
});
