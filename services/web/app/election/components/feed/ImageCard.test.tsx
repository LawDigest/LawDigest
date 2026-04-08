import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import ImageCard from './ImageCard';

const mockItem = {
  type: 'image' as const,
  id: 'img-1',
  groupName: '국민의힘 서울시당',
  partyName: '국민의힘',
  content: '주말 서울 광장 그린업 프로젝트 성공적으로 마쳤습니다!',
  images: [
    { src: 'https://example.com/img1.jpg', alt: '나무 심기 행사' },
    { src: 'https://example.com/img2.jpg', alt: '자원봉사자들' },
  ],
  publishedAt: '2026-04-02T14:00:00Z',
};

describe('ImageCard', () => {
  it('그룹명을 렌더링한다', () => {
    render(<ImageCard item={mockItem} />);
    expect(screen.getByText('국민의힘 서울시당')).toBeInTheDocument();
  });

  it('본문 내용을 렌더링한다', () => {
    render(<ImageCard item={mockItem} />);
    expect(screen.getByText('주말 서울 광장 그린업 프로젝트 성공적으로 마쳤습니다!')).toBeInTheDocument();
  });

  it('타입 칩을 렌더링한다', () => {
    render(<ImageCard item={mockItem} />);
    expect(screen.getByText('이미지')).toBeInTheDocument();
  });
});
