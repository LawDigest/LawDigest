export const ELECTION_FAMILY = {
  local: 'local',
  assembly: 'assembly',
  president: 'president',
} as const;

export const ELECTION_STATUS = {
  upcoming: 'upcoming',
  current: 'current',
  past: 'past',
} as const;

export const ELECTION_UI_TEMPLATE = {
  regional: 'REGIONAL',
  candidate: 'CANDIDATE',
} as const;

export const ELECTION_VIEW_MODE = {
  result: 'RESULT',
} as const;
