import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import FeedTypeChip from './FeedTypeChip';

describe('FeedTypeChip', () => {
  it('여론조사 타입을 렌더링한다', () => {
    render(<FeedTypeChip type="poll" />);
    expect(screen.getByText('여론조사')).toBeInTheDocument();
  });

  it('SNS 타입을 렌더링한다', () => {
    render(<FeedTypeChip type="sns" platform="twitter" />);
    expect(screen.getByText('SNS')).toBeInTheDocument();
  });

  it('법안 타입을 렌더링한다', () => {
    render(<FeedTypeChip type="bill" />);
    expect(screen.getByText('법안')).toBeInTheDocument();
  });

  it('영상 타입을 렌더링한다', () => {
    render(<FeedTypeChip type="youtube" />);
    expect(screen.getByText('영상')).toBeInTheDocument();
  });

  it('이미지 타입을 렌더링한다', () => {
    render(<FeedTypeChip type="image" />);
    expect(screen.getByText('이미지')).toBeInTheDocument();
  });
});
