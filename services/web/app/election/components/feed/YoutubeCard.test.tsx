import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import YoutubeCard from './YoutubeCard';

const mockItem = {
  type: 'youtube' as const,
  id: 'yt-1',
  candidateName: '홍길동',
  partyName: '더불어민주당',
  channelName: '더불어민주당 공식 채널',
  title: '타운홀 미팅 하이라이트',
  thumbnailUrl: 'https://example.com/thumb.jpg',
  publishedAt: '2026-04-03T09:00:00Z',
  likes: 1200,
  comments: 342,
};

describe('YoutubeCard', () => {
  it('영상 제목을 렌더링한다', () => {
    render(<YoutubeCard item={mockItem} />);
    expect(screen.getByText('타운홀 미팅 하이라이트')).toBeInTheDocument();
  });

  it('채널명을 렌더링한다', () => {
    render(<YoutubeCard item={mockItem} />);
    expect(screen.getByText('더불어민주당 공식 채널')).toBeInTheDocument();
  });

  it('재생 버튼에 aria-label이 있다', () => {
    render(<YoutubeCard item={mockItem} />);
    expect(screen.getByRole('button', { name: '영상 재생' })).toBeInTheDocument();
  });

  it('타입 칩을 렌더링한다', () => {
    render(<YoutubeCard item={mockItem} />);
    expect(screen.getByText('영상')).toBeInTheDocument();
  });
});
