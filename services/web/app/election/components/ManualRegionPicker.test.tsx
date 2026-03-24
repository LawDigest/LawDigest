import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import ManualRegionPicker from './ManualRegionPicker';

describe('ManualRegionPicker', () => {
  it('submits the selected province as the starting region', () => {
    const onSubmit = vi.fn();

    render(<ManualRegionPicker onSubmit={onSubmit} onCancel={vi.fn()} />);

    fireEvent.click(screen.getByRole('button', { name: '부산광역시' }));
    fireEvent.click(screen.getByRole('button', { name: '부산광역시 보기' }));

    expect(onSubmit).toHaveBeenCalledWith({
      regionCode: '26',
      regionName: '부산광역시',
      regionType: 'PROVINCE',
    });
  });

  it('supports starting from the national view', () => {
    const onSubmit = vi.fn();

    render(<ManualRegionPicker onSubmit={onSubmit} onCancel={vi.fn()} />);

    fireEvent.click(screen.getByRole('button', { name: /전국에서 보기/ }));
    fireEvent.click(screen.getByRole('button', { name: '전국에서 시작' }));

    expect(onSubmit).toHaveBeenCalledWith({
      regionCode: '00',
      regionName: '대한민국',
      regionType: 'NATIONAL',
    });
  });
});
