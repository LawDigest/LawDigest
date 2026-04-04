// services/web/app/election/components/shared/DistrictMapPicker.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import DistrictMapPicker from './DistrictMapPicker';

vi.mock('../ManualRegionPicker', () => ({
  default: ({
    onSubmit,
  }: {
    onSubmit: (v: { regionCode: string; regionName: string; regionType: string }) => void;
  }) => (
    <button
      type="button"
      onClick={() => onSubmit({ regionCode: '11', regionName: '서울특별시', regionType: 'PROVINCE' })}>
      서울특별시 선택
    </button>
  ),
}));

describe('DistrictMapPicker', () => {
  it('초기에는 지역 선택 UI를 보여준다', () => {
    render(<DistrictMapPicker selected={null} onSelect={vi.fn()} />);
    expect(screen.getByText('서울특별시 선택')).toBeInTheDocument();
  });

  it('지역 선택 시 onSelect를 호출한다', () => {
    const onSelect = vi.fn();
    render(<DistrictMapPicker selected={null} onSelect={onSelect} />);
    fireEvent.click(screen.getByText('서울특별시 선택'));
    expect(onSelect).toHaveBeenCalledWith({ regionCode: '11', regionName: '서울특별시' });
  });

  it('선택된 지역이 있으면 칩으로 표시하고 지도를 접는다', () => {
    render(<DistrictMapPicker selected={{ regionCode: '11', regionName: '서울특별시' }} onSelect={vi.fn()} />);
    expect(screen.getByText('서울특별시')).toBeInTheDocument();
    expect(screen.queryByText('서울특별시 선택')).not.toBeInTheDocument();
  });
});
