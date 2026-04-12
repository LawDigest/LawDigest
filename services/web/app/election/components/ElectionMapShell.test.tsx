import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import ElectionMapShell from './ElectionMapShell';

const mockUseGetElectionSelector = vi.fn();
const mockUseSearchParams = vi.fn();
const mockPush = vi.fn();

vi.mock('@/components', () => ({
  Layout: ({ children }: { children: React.ReactNode }) => <div data-testid="layout-shell">{children}</div>,
}));

vi.mock('../apis/queries', () => ({
  useGetElectionSelector: () => mockUseGetElectionSelector(),
}));

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush }),
  useSearchParams: () => mockUseSearchParams(),
}));

vi.mock('./ElectionHeader', () => ({
  default: ({ electionName }: { electionName: string }) => <div data-testid="election-header">{electionName}</div>,
}));

vi.mock('./ElectionSelector', () => ({
  default: () => <div data-testid="election-selector">selector</div>,
}));

vi.mock('./ElectionInnerTabBar', () => ({
  default: () => <div data-testid="inner-tab-bar">tabs</div>,
}));

vi.mock('./ElectionMapTabView', () => ({
  default: () => <div data-testid="election-map-tab-view">map-design</div>,
}));

vi.mock('./RegionalElectionView', () => ({
  default: () => <div data-testid="regional-election-view">regional-view</div>,
}));

vi.mock('./PresidentialElectionView', () => ({
  default: () => <div data-testid="presidential-election-view">presidential-view</div>,
}));

vi.mock('./ElectionFeedView', () => ({
  default: () => <div data-testid="feed-view">feed</div>,
}));

vi.mock('./ElectionPollView', () => ({
  default: () => <div data-testid="poll-view">poll</div>,
}));

vi.mock('./ElectionDistrictView', () => ({
  default: () => <div data-testid="district-view">district</div>,
}));

describe('ElectionMapShell', () => {
  it('지도 탭에서는 기존 ElectionMapTabView 디자인을 렌더링한다', () => {
    mockUseSearchParams.mockReturnValue({
      get: (key: string) => (key === 'tab' ? 'map' : null),
      toString: () => 'tab=map',
    });

    mockUseGetElectionSelector.mockReturnValue({
      data: {
        data: {
          default_election_id: '20250603',
          elections: [
            {
              election_id: '20250603',
              election_name: '제21대 대통령선거',
              election_date: '20250603',
              upcoming: false,
            },
          ],
        },
      },
    });

    render(<ElectionMapShell />);

    expect(screen.getByTestId('election-map-tab-view')).toBeInTheDocument();
    expect(screen.queryByTestId('regional-election-view')).not.toBeInTheDocument();
    expect(screen.queryByTestId('presidential-election-view')).not.toBeInTheDocument();
  });
});
