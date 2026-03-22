export const STAGE_TAB = {
  reception: 'reception',
  committeeJudge: 'committeeJudge',
  review: 'review',
  promulgation: 'promulgation',
} as const;

export const BILL_STAGE = {
  ...STAGE_TAB,
  districtJudge: 'districtJudge',
  transfer: 'transfer',
} as const;

export const STAGE_TAB_KO = {
  reception: '접수',
  committeeJudge: '위원회 심사',
  review: '본회의 심의',
  promulgation: '공포',
} as const;

export const BILL_STAGE_KO = {
  ...STAGE_TAB_KO,
  districtJudge: '체계지구 심사',
  transfer: '정부 이송',
} as const;

export const PROGRESS_STAGE = {
  reception: 'reception',
  committeeJudge: 'committeeJudge',
  districtJudge: 'districtJudge',
  review: 'review',
  transfer: 'transfer',
  promulgation: 'promulgation',
};

export const PROGRESS_STAGE_KO = {
  reception: '접수',
  committeeJudge: '위원회 심사',
  districtJudge: '체계지구 심사',
  review: '본회의 심의',
  transfer: '정부 이송',
  promulgation: '공포',
};

export const FEED_TAB = {
  sortedByLatest: 'sorted_by_latest',
  sortedByPopularity: 'sorted_by_popularity',
} as const;

export const BILL_TAB = {
  representProposer: 'represent_proposer',
  publicProposer: 'public_proposer',
} as const;

export const BILL_TAB_KO = {
  representProposer: '대표발의한 법안',
  publicProposer: '공동발의한 법안',
} as const;

export const SEARCH_TAB = {
  bill: 'bill',
  congressmanParty: 'congressmanParty',
} as const;

export const SEARCH_TAB_KO = {
  bill: '법안',
  congressmanParty: '의원/정당',
} as const;

export const PROPORTIONAL_TAB = {
  promise: 'promise',
  candidate: 'candidate',
};

export const PROPORTIONAL_TAB_KO = {
  promise: '정당 공약',
  candidate: '후보자 명단',
};
