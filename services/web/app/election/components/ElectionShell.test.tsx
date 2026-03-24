import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import ElectionShell from './ElectionShell';

const mockUseGetElectionSelector = vi.fn();
const mockResolveMutateAsync = vi.fn();
const mockConfirmMutateAsync = vi.fn();
let mockResolveIsPending = false;
let mockConfirmIsPending = false;

vi.mock('@/components', () => ({
  Layout: ({ children }: { children: React.ReactNode }) => <div data-testid="layout-shell">{children}</div>,
}));

vi.mock('../apis/queries', () => ({
  useGetElectionSelector: () => mockUseGetElectionSelector(),
  usePostElectionRegionResolve: () => ({
    mutateAsync: mockResolveMutateAsync,
    isPending: mockResolveIsPending,
  }),
  usePostElectionRegionConfirm: () => ({
    mutateAsync: mockConfirmMutateAsync,
    isPending: mockConfirmIsPending,
  }),
}));

vi.mock('./ElectionModeTabs', () => ({
  default: ({ selectedKey }: { selectedKey: string }) => <div data-testid="mode-tabs">{selectedKey}</div>,
}));

vi.mock('./RegionalElectionView', () => ({
  default: ({ electionId, regionCode, regionName }: { electionId: string; regionCode: string; regionName: string }) => (
    <div data-testid="regional-election-view">
      {electionId}:{regionCode}:{regionName}
    </div>
  ),
}));

vi.mock('./PresidentialElectionView', () => ({
  default: ({ electionId }: { electionId: string }) => <div data-testid="presidential-election-view">{electionId}</div>,
}));

interface ButtonLikeProps {
  onClick: () => void;
}

vi.mock('./EmptyRegionState', () => ({
  default: ({
    onResolve,
    onManualSelect,
    description,
    isPending,
  }: ButtonLikeProps & { description: string; isPending?: boolean }) => (
    <div>
      <p>{description}</p>
      <p>{isPending ? 'pending' : 'idle'}</p>
      <button type="button" onClick={onResolve}>
        현재 위치로 지역 찾기
      </button>
      <button type="button" onClick={onManualSelect}>
        직접 지역 선택
      </button>
    </div>
  ),
}));

vi.mock('./RegionConfirmCard', () => ({
  default: ({
    regionName,
    onConfirm,
    onManualSelect,
  }: {
    regionName: string;
    onConfirm: () => void;
    onManualSelect: () => void;
  }) => (
    <div>
      <p>{regionName}</p>
      <button type="button" onClick={onConfirm}>
        이 지역으로 확정
      </button>
      <button type="button" onClick={onManualSelect}>
        직접 수정
      </button>
    </div>
  ),
}));

vi.mock('./ManualRegionPicker', () => ({
  default: ({ onCancel }: { onCancel: () => void }) => (
    <div>
      <p>manual-picker</p>
      <button type="button" onClick={onCancel}>
        닫기
      </button>
    </div>
  ),
}));

const selectorResponse = {
  default_election_id: 'president-2027',
  elections: [
    {
      election_id: 'president-2027',
      election_name: '제21대 대통령선거',
      election_date: '2027-03-09',
      upcoming: true,
    },
    {
      election_id: 'local-2026',
      election_name: '제9회 전국동시지방선거',
      election_date: '2026-06-03',
      upcoming: true,
    },
    {
      election_id: 'assembly-2024',
      election_name: '제22대 국회의원선거',
      election_date: '2024-04-10',
      upcoming: false,
    },
  ],
};

const createDeferred = <T,>() => {
  let resolvePromise: (value: T) => void = () => {};
  const promise = new Promise<T>((resolve) => {
    resolvePromise = resolve;
  });

  return {
    promise,
    resolve: resolvePromise,
  };
};

describe('ElectionShell', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockResolveIsPending = false;
    mockConfirmIsPending = false;

    mockUseGetElectionSelector.mockReturnValue({
      data: { data: selectorResponse },
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });

    mockConfirmMutateAsync.mockResolvedValue({
      data: {
        election_id: 'local-2026',
        state: 'confirmed',
        confirmation_required: false,
        suggested_region_type: 'DISTRICT',
        suggested_region_code: 'seoul-jongno',
        suggested_region_name: '서울 종로구',
        manual_correction_available: true,
        deny_available: false,
      },
    });

    Object.defineProperty(window.navigator, 'geolocation', {
      configurable: true,
      value: {
        getCurrentPosition: vi.fn((success: PositionCallback) => {
          success({
            coords: {
              latitude: 37.57,
              longitude: 126.98,
              accuracy: 1,
              altitude: null,
              altitudeAccuracy: null,
              heading: null,
              speed: null,
              toJSON: () => ({}),
            },
            timestamp: Date.now(),
            toJSON: () => ({}),
          } as GeolocationPosition);
        }),
      },
    });
  });

  it('ignores a stale resolve response after the user switches elections', async () => {
    const deferred = createDeferred<{
      data: {
        election_id: string;
        state: 'confirmed';
        confirmation_required: false;
        suggested_region_type: 'DISTRICT';
        suggested_region_code: string;
        suggested_region_name: string;
        manual_correction_available: true;
        deny_available: false;
      };
    }>();

    mockResolveMutateAsync.mockReturnValueOnce(deferred.promise);

    render(<ElectionShell />);

    fireEvent.click(screen.getByRole('button', { name: '현재 위치로 지역 찾기' }));
    fireEvent.change(screen.getByLabelText('선거 선택'), {
      target: { value: 'assembly-2024' },
    });

    await act(async () => {
      deferred.resolve({
        data: {
          election_id: 'local-2026',
          state: 'confirmed',
          confirmation_required: false,
          suggested_region_type: 'DISTRICT',
          suggested_region_code: 'seoul-jongno',
          suggested_region_name: '서울 종로구',
          manual_correction_available: true,
          deny_available: false,
        },
      });

      await deferred.promise;
    });

    await waitFor(() => {
      expect(screen.getByLabelText('선거 선택')).toHaveValue('assembly-2024');
    });

    expect(screen.queryByTestId('regional-election-view')).not.toBeInTheDocument();
    expect(screen.queryByText('서울 종로구')).not.toBeInTheDocument();
  });

  it('recovers to the manual picker when region resolution fails', async () => {
    mockResolveMutateAsync.mockRejectedValueOnce(new Error('resolve failed'));

    render(<ElectionShell />);

    fireEvent.click(screen.getByRole('button', { name: '현재 위치로 지역 찾기' }));

    await waitFor(() => {
      expect(screen.getByText('manual-picker')).toBeInTheDocument();
    });

    expect(
      screen.getByText('지역 확인 요청에 실패했습니다. 직접 지역을 선택하거나 다시 시도해 주세요.'),
    ).toBeInTheDocument();
  });

  it('does not leak stale pending state into the newly selected election', async () => {
    const deferred = createDeferred<{
      data: {
        election_id: string;
        state: 'confirmed';
        confirmation_required: false;
        suggested_region_type: 'DISTRICT';
        suggested_region_code: string;
        suggested_region_name: string;
        manual_correction_available: true;
        deny_available: false;
      };
    }>();

    mockResolveMutateAsync.mockImplementationOnce(() => {
      mockResolveIsPending = true;
      return deferred.promise;
    });

    render(<ElectionShell />);

    fireEvent.click(screen.getByRole('button', { name: '현재 위치로 지역 찾기' }));
    fireEvent.change(screen.getByLabelText('선거 선택'), {
      target: { value: 'assembly-2024' },
    });

    await waitFor(() => {
      expect(screen.getByLabelText('선거 선택')).toHaveValue('assembly-2024');
    });

    expect(screen.getByText('idle')).toBeInTheDocument();
    expect(screen.queryByText('pending')).not.toBeInTheDocument();

    await act(async () => {
      mockResolveIsPending = false;
      deferred.resolve({
        data: {
          election_id: 'local-2026',
          state: 'confirmed',
          confirmation_required: false,
          suggested_region_type: 'DISTRICT',
          suggested_region_code: 'seoul-jongno',
          suggested_region_name: '서울 종로구',
          manual_correction_available: true,
          deny_available: false,
        },
      });

      await deferred.promise;
    });
  });

  it('renders the presidential candidate-centric view when the president election is selected', async () => {
    render(<ElectionShell />);

    fireEvent.change(screen.getByLabelText('선거 선택'), {
      target: { value: 'president-2027' },
    });

    await waitFor(() => {
      expect(screen.getByTestId('presidential-election-view')).toBeInTheDocument();
    });

    expect(screen.queryByTestId('regional-election-view')).not.toBeInTheDocument();
  });
});
