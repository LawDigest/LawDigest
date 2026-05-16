import { describe, expect, it } from 'vitest';
import { getPartyColor, PARTY_COLOR, UNKNOWN_PARTY_COLOR } from './party';

describe('getPartyColor', () => {
  it('returns the canonical party color for exact and partial party names', () => {
    expect(getPartyColor('더불어민주당')).toBe(PARTY_COLOR.더불어민주당);
    expect(getPartyColor('국민의힘 후보')).toBe(PARTY_COLOR.국민의힘);
    expect(getPartyColor('조국')).toBe(PARTY_COLOR.조국혁신당);
  });

  it('uses the neutral fallback for unknown or empty party names', () => {
    expect(getPartyColor('알 수 없음')).toBe(UNKNOWN_PARTY_COLOR);
    expect(getPartyColor(null)).toBe(UNKNOWN_PARTY_COLOR);
  });
});
