import { ElectionId, ElectionSelectorItem, ElectionSelectorResponse } from '@/types';

const UPCOMING_LOCAL_ELECTION_ID = 'local-2026';

const getElectionPriority = ({ election_id, upcoming }: ElectionSelectorItem) => {
  if (election_id === UPCOMING_LOCAL_ELECTION_ID) {
    return 0;
  }

  if (upcoming) {
    return 1;
  }

  return 2;
};

export const compareElectionSelectorItems = (left: ElectionSelectorItem, right: ElectionSelectorItem) => {
  const priorityDiff = getElectionPriority(left) - getElectionPriority(right);
  if (priorityDiff !== 0) {
    return priorityDiff;
  }

  const dateDiff = new Date(right.election_date).getTime() - new Date(left.election_date).getTime();
  if (dateDiff !== 0) {
    return dateDiff;
  }

  return left.election_name.localeCompare(right.election_name, 'ko');
};

export const getDefaultElectionId = (selector: ElectionSelectorResponse): ElectionId => {
  if (selector.elections.some(({ election_id }) => election_id === UPCOMING_LOCAL_ELECTION_ID)) {
    return UPCOMING_LOCAL_ELECTION_ID;
  }

  if (selector.default_election_id) {
    return selector.default_election_id;
  }

  return [...selector.elections].sort(compareElectionSelectorItems)[0]?.election_id ?? UPCOMING_LOCAL_ELECTION_ID;
};
