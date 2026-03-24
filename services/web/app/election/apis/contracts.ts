import {
  ElectionCandidateId,
  ElectionId,
  ElectionQueryContract,
  ElectionRegionResolveRequest,
  ElectionRegionResolveState,
} from '@/types';

export const ELECTION_QUERY_CONTRACT = {
  selectorKey: ['/election', 'selector'] as const,
  candidateDetailKey: ['/election', 'candidate-detail', '' as ElectionId, '' as ElectionCandidateId] as const,
  resolveRequest: {
    election_id: '' as ElectionId,
    latitude: null,
    longitude: null,
    region_code: null,
    region_type: null,
    region_name: null,
    permission_status: 'idle',
  } satisfies ElectionRegionResolveRequest,
  resolveResponseState: 'requesting-permission' as ElectionRegionResolveState,
} satisfies ElectionQueryContract;
