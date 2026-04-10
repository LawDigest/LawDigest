// utils.test.ts
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { timeAgo, formatCount, formatDate } from './utils';

describe('timeAgo', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-04-08T12:00:00Z'));
  });
  afterEach(() => {
    vi.useRealTimers();
  });

  it('1시간 이내면 분 단위로 반환한다', () => {
    expect(timeAgo('2026-04-08T11:30:00Z')).toBe('30분 전');
  });

  it('24시간 이내면 시간 단위로 반환한다', () => {
    expect(timeAgo('2026-04-08T06:00:00Z')).toBe('6시간 전');
  });

  it('24시간 이상이면 일 단위로 반환한다', () => {
    expect(timeAgo('2026-04-06T12:00:00Z')).toBe('2일 전');
  });
});

describe('formatCount', () => {
  it('undefined이면 0을 반환한다', () => {
    expect(formatCount(undefined)).toBe('0');
  });

  it('0이면 0을 반환한다', () => {
    expect(formatCount(0)).toBe('0');
  });

  it('1000 미만이면 숫자 그대로 반환한다', () => {
    expect(formatCount(342)).toBe('342');
  });

  it('1000 이상이면 k 단위로 반환한다', () => {
    expect(formatCount(1200)).toBe('1.2k');
  });
});

describe('formatDate', () => {
  it('ISO 날짜 문자열을 한국어 월/일 형태로 반환한다', () => {
    expect(formatDate('2026-03-15')).toBe('3월 15일');
  });

  it('1월 날짜를 올바르게 반환한다', () => {
    expect(formatDate('2026-01-05')).toBe('1월 5일');
  });
});
