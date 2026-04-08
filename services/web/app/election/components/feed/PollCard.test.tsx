import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import PollCard from './PollCard';

const mockItem = {
  type: 'poll' as const,
  id: 'poll-1',
  pollster: '한국갤럽',
  publishedAt: '2026-04-03T00:00:00Z',
  results: [
    { partyName: '더불어민주당', pct: 47.3, delta: 1.2, color: '#152484' },
    { partyName: '국민의힘', pct: 43.1, delta: -0.8, color: '#C9151E' },
  ],
  region: '서울특별시',
};

describe('PollCard', () => {
  it('조사기관명을 렌더링한다', () => {
    render(<PollCard item={mockItem} />);
    expect(screen.getByText('한국갤럽')).toBeInTheDocument();
  });

  it('지역을 렌더링한다', () => {
    render(<PollCard item={mockItem} />);
    expect(screen.getByText('서울특별시')).toBeInTheDocument();
  });

  it('모든 정당 결과를 렌더링한다', () => {
    render(<PollCard item={mockItem} />);
    expect(screen.getByText('더불어민주당')).toBeInTheDocument();
    expect(screen.getByText('국민의힘')).toBeInTheDocument();
  });

  it('퍼센트를 렌더링한다', () => {
    render(<PollCard item={mockItem} />);
    expect(screen.getByText('47.3%')).toBeInTheDocument();
  });

  it('타입 칩을 렌더링한다', () => {
    render(<PollCard item={mockItem} />);
    expect(screen.getByText('여론조사')).toBeInTheDocument();
  });
});
