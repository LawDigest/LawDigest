'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  ElectionId,
  ElectionCandidateId,
  ElectionRegionCode,
  ElectionRegionResolveRequest,
  ElectionRegionType,
  ElectionViewMode,
} from '@/types';
import {
  postElectionRegionConfirm,
  postElectionRegionResolve,
  getElectionCandidateDetail,
  getElectionCandidates,
  getElectionMap,
  getElectionOverview,
  getElectionRegionPanel,
  getElectionSelector,
} from './apis';

type ElectionQueryRoot = '/election';

type ElectionQueryKeys = {
  selector: readonly [ElectionQueryRoot, 'selector'];
  overview: (args: {
    electionId: ElectionId;
    regionType: ElectionRegionType;
    regionCode: ElectionRegionCode;
  }) => readonly [ElectionQueryRoot, 'overview', ElectionId, ElectionRegionType, ElectionRegionCode];
  map: (args: {
    electionId: ElectionId;
    depth: ElectionRegionType;
    regionCode: ElectionRegionCode;
    viewMode: ElectionViewMode;
  }) => readonly [ElectionQueryRoot, 'map', ElectionId, ElectionRegionType, ElectionRegionCode, ElectionViewMode];
  regionPanel: (args: {
    electionId: ElectionId;
    depth: ElectionRegionType;
    regionCode: ElectionRegionCode;
    officeType?: string | null;
  }) => readonly [
    ElectionQueryRoot,
    'region-panel',
    ElectionId,
    ElectionRegionType,
    ElectionRegionCode,
    string | null | undefined,
  ];
  candidates: (args: {
    electionId: ElectionId;
    regionCode: ElectionRegionCode;
    officeType?: string | null;
  }) => readonly [ElectionQueryRoot, 'candidates', ElectionId, ElectionRegionCode, string | null | undefined];
  candidateDetail: (args: {
    electionId: ElectionId;
    candidateId: ElectionCandidateId;
  }) => readonly [ElectionQueryRoot, 'candidate-detail', ElectionId, ElectionCandidateId];
};

export const ELECTION_QUERY_KEYS = {
  selector: ['/election', 'selector'] as const,
  overview: ({ electionId, regionType, regionCode }) =>
    ['/election', 'overview', electionId, regionType, regionCode] as const,
  map: ({ electionId, depth, regionCode, viewMode }) =>
    ['/election', 'map', electionId, depth, regionCode, viewMode] as const,
  regionPanel: ({ electionId, depth, regionCode, officeType }) =>
    ['/election', 'region-panel', electionId, depth, regionCode, officeType] as const,
  candidates: ({ electionId, regionCode, officeType }) =>
    ['/election', 'candidates', electionId, regionCode, officeType] as const,
  candidateDetail: ({ electionId, candidateId }) => ['/election', 'candidate-detail', electionId, candidateId] as const,
} satisfies ElectionQueryKeys;

export const ELECTION_MUTATION_KEYS = {
  regionResolve: ['/election', 'region-resolve'] as const,
  regionConfirm: ['/election', 'region-confirm'] as const,
} as const;

export const useGetElectionSelector = () =>
  useQuery({
    queryKey: ELECTION_QUERY_KEYS.selector,
    queryFn: () => getElectionSelector(),
  });

export const useGetElectionOverview = (
  electionId: ElectionId,
  regionType: ElectionRegionType,
  regionCode: ElectionRegionCode,
) =>
  useQuery({
    queryKey: ELECTION_QUERY_KEYS.overview({ electionId, regionType, regionCode }),
    queryFn: () => getElectionOverview(electionId, regionType, regionCode),
  });

export const useGetElectionMap = (
  electionId: ElectionId,
  depth: ElectionRegionType,
  regionCode: ElectionRegionCode,
  viewMode: ElectionViewMode,
) =>
  useQuery({
    queryKey: ELECTION_QUERY_KEYS.map({ electionId, depth, regionCode, viewMode }),
    queryFn: () => getElectionMap(electionId, depth, regionCode, viewMode),
  });

export const useGetElectionRegionPanel = (
  electionId: ElectionId,
  depth: ElectionRegionType,
  regionCode: ElectionRegionCode,
  officeType?: string | null,
) =>
  useQuery({
    queryKey: ELECTION_QUERY_KEYS.regionPanel({ electionId, depth, regionCode, officeType }),
    queryFn: () => getElectionRegionPanel(electionId, depth, regionCode, officeType),
  });

export const useGetElectionCandidates = (
  electionId: ElectionId,
  regionCode: ElectionRegionCode,
  officeType?: string | null,
) =>
  useQuery({
    queryKey: ELECTION_QUERY_KEYS.candidates({ electionId, regionCode, officeType }),
    queryFn: () => getElectionCandidates(electionId, regionCode, officeType),
  });

export const useGetElectionCandidateDetail = (electionId: ElectionId, candidateId: ElectionCandidateId) =>
  useQuery({
    queryKey: ELECTION_QUERY_KEYS.candidateDetail({ electionId, candidateId }),
    queryFn: () => getElectionCandidateDetail(electionId, candidateId),
  });

const invalidateElectionQueries = (queryClient: ReturnType<typeof useQueryClient>) => {
  queryClient.invalidateQueries({ queryKey: ['/election'] });
};

export const usePostElectionRegionResolve = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationKey: ELECTION_MUTATION_KEYS.regionResolve,
    mutationFn: (body: ElectionRegionResolveRequest) => postElectionRegionResolve(body),
    onSuccess: () => {
      invalidateElectionQueries(queryClient);
    },
  });
};

export const usePostElectionRegionConfirm = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationKey: ELECTION_MUTATION_KEYS.regionConfirm,
    mutationFn: (body: ElectionRegionResolveRequest) => postElectionRegionConfirm(body),
    onSuccess: () => {
      invalidateElectionQueries(queryClient);
    },
  });
};
