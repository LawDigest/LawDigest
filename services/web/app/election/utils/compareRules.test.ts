import { describe, expect, it } from 'vitest';
import { compareElectionSelectorItems, getDefaultElectionId } from './compareRules';

describe('compareRules', () => {
  it('prioritizes the 2026 local election ahead of other elections', () => {
    const items = [
      {
        election_id: 'local-2022',
        election_name: '제8회 전국동시지방선거',
        election_date: '2022-06-01',
        upcoming: false,
      },
      {
        election_id: 'president-2027',
        election_name: '제21대 대통령선거',
        election_date: '2027-03-03',
        upcoming: true,
      },
      {
        election_id: 'local-2026',
        election_name: '제9회 전국동시지방선거',
        election_date: '2026-06-03',
        upcoming: true,
      },
    ];

    expect([...items].sort(compareElectionSelectorItems).map(({ election_id }) => election_id)).toEqual([
      'local-2026',
      'president-2027',
      'local-2022',
    ]);
  });

  it('uses the 2026 local election as the default selection before selector defaults', () => {
    expect(
      getDefaultElectionId({
        default_election_id: 'president-2027',
        elections: [
          {
            election_id: 'president-2027',
            election_name: '제21대 대통령선거',
            election_date: '2027-03-03',
            upcoming: true,
          },
          {
            election_id: 'local-2026',
            election_name: '제9회 전국동시지방선거',
            election_date: '2026-06-03',
            upcoming: true,
          },
        ],
      }),
    ).toBe('local-2026');
  });
});
