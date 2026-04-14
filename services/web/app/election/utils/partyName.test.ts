import { describe, expect, it } from 'vitest';
import { aggregatePartySnapshots, normalizePartyName } from './partyName';

describe('partyName utils', () => {
  it('normalizes unknown and other-party variants to undecided', () => {
    expect(normalizePartyName('잘 모르겠다')).toBe('undecided');
    expect(normalizePartyName('잘 모르겠 다')).toBe('undecided');
    expect(normalizePartyName('잘 모르 겠다')).toBe('undecided');
    expect(normalizePartyName('그 외 다른 정당')).toBe('undecided');
    expect(normalizePartyName('그 외 정당')).toBe('undecided');
  });

  it('aggregates undecided-like variants into a single bucket', () => {
    expect(
      aggregatePartySnapshots([
        { party_name: '그 외 다른 정당', percentage: 4.1 },
        { party_name: '그 외 정당', percentage: 2.2 },
        { party_name: '잘 모르겠다', percentage: 3.0 },
        { party_name: '더불어민주당', percentage: 41.2 },
      ]),
    ).toEqual([
      { party_name: 'undecided', percentage: 9.3 },
      { party_name: '더불어민주당', percentage: 41.2 },
    ]);
  });
});
