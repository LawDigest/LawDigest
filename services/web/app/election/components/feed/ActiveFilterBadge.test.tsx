import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import ActiveFilterBadge from './ActiveFilterBadge';

describe('ActiveFilterBadge', () => {
  it('label을 렌더링한다', () => {
    render(<ActiveFilterBadge label="더불어민주당" onClear={() => {}} />);
    expect(screen.getByText('더불어민주당 필터 적용 중')).toBeInTheDocument();
  });

  it('해제 버튼 클릭 시 onClear를 호출한다', () => {
    const onClear = vi.fn();
    render(<ActiveFilterBadge label="국민의힘" onClear={onClear} />);
    fireEvent.click(screen.getByRole('button', { name: /해제/ }));
    expect(onClear).toHaveBeenCalledTimes(1);
  });
});
