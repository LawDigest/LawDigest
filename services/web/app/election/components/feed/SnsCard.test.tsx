import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import SnsCard from './SnsCard';

const mockItem = {
  type: 'sns' as const,
  id: 'sns-1',
  platform: 'twitter' as const,
  candidateName: '이순신',
  partyName: '국민의힘',
  content: '디지털 미래를 위한 공약을 발표합니다.',
  publishedAt: '2026-04-03T11:30:00Z',
  originalUrl: 'https://twitter.com/example',
  region: '서울특별시',
  likes: 156,
  comments: 18,
  retweets: 42,
};

describe('SnsCard', () => {
  it('후보자명을 렌더링한다', () => {
    render(<SnsCard item={mockItem} />);
    expect(screen.getByText('이순신')).toBeInTheDocument();
  });

  it('정당명을 렌더링한다', () => {
    render(<SnsCard item={mockItem} />);
    expect(screen.getByText('국민의힘')).toBeInTheDocument();
  });

  it('본문 내용을 렌더링한다', () => {
    render(<SnsCard item={mockItem} />);
    expect(screen.getByText('디지털 미래를 위한 공약을 발표합니다.')).toBeInTheDocument();
  });

  it('좋아요 수를 렌더링한다', () => {
    render(<SnsCard item={mockItem} />);
    expect(screen.getByText('156')).toBeInTheDocument();
  });

  it('타입 칩을 렌더링한다', () => {
    render(<SnsCard item={mockItem} />);
    expect(screen.getByText('SNS')).toBeInTheDocument();
  });
});
