import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import ElectionHeader from './ElectionHeader';

describe('ElectionHeader', () => {
  it('유효하지 않은 날짜가 들어와도 NaN을 렌더링하지 않는다', () => {
    render(<ElectionHeader electionName="제21대 대통령선거" electionDate={new Date('invalid-date')} />);

    expect(screen.queryByText('NaN')).not.toBeInTheDocument();
    expect(screen.getByText('날짜 미정')).toBeInTheDocument();
  });

  it('D-day를 이전 텍스트형 표기로 렌더링한다', () => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    render(<ElectionHeader electionName="제21대 대통령선거" electionDate={today} />);

    expect(screen.getByText('D-')).toBeInTheDocument();
    expect(screen.getByText('0')).toBeInTheDocument();
    expect(screen.getByText('D-').parentElement).toHaveClass('text-theme-alert');
    expect(screen.getByText('D-').parentElement).not.toHaveClass('rounded-full');
  });
});
