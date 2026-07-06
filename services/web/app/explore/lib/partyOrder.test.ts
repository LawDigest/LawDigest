import { describe, expect, it } from 'vitest';
import { getPartySpectrumRank } from './partyOrder';

describe('getPartySpectrumRank', () => {
  it('진보 소수정당이 더불어민주당보다 왼쪽(작은 순위)이다', () => {
    expect(getPartySpectrumRank('조국혁신당')).toBeLessThan(getPartySpectrumRank('더불어민주당'));
    expect(getPartySpectrumRank('진보당')).toBeLessThan(getPartySpectrumRank('조국혁신당'));
  });

  it('국민의힘이 더불어민주당보다 오른쪽(큰 순위)이다', () => {
    expect(getPartySpectrumRank('국민의힘')).toBeGreaterThan(getPartySpectrumRank('더불어민주당'));
  });

  it('부분 일치로 매칭하고, 알 수 없는 정당은 중앙에 배치한다', () => {
    expect(getPartySpectrumRank('국민의힘 원내')).toBe(getPartySpectrumRank('국민의힘'));
    const unknown = getPartySpectrumRank('무소속');
    expect(unknown).toBeGreaterThan(getPartySpectrumRank('조국혁신당'));
    expect(unknown).toBeLessThan(getPartySpectrumRank('국민의힘'));
  });
});
