import { AxiosError } from 'axios';
import http from '@/api';
import {
  ElectionCandidateId,
  ElectionCandidateDetailResponse,
  ElectionCandidateListResponse,
  ElectionId,
  ElectionMapResponse,
  ElectionOverviewResponse,
  ElectionRegionCode,
  ElectionRegionPanelResponse,
  ElectionRegionResolveRequest,
  ElectionRegionResolveResponse,
  ElectionRegionType,
  ElectionViewMode,
  ElectionSelectorResponse,
  BaseResponse,
} from '@/types';
import {
  getMockElectionCandidateDetail,
  getMockElectionCandidates,
  getMockElectionMap,
  getMockElectionOverview,
  getMockElectionRegionPanel,
  getMockElectionSelector,
  postMockElectionRegionConfirm,
  postMockElectionRegionResolve,
} from './mock';

const publicDomain = process.env.NEXT_PUBLIC_DOMAIN ?? '';
const shouldUseElectionFallback =
  publicDomain.includes('dev.lawdigest.net') ||
  publicDomain.includes('test.lawdigest.net') ||
  publicDomain.includes('127.0.0.1') ||
  publicDomain.includes('localhost');

const shouldRecoverWithMock = (error: unknown) => {
  if (!shouldUseElectionFallback) {
    return false;
  }

  if (!(error instanceof AxiosError)) {
    return true;
  }

  if (!error.response) {
    return true;
  }

  return error.response.status === 401 || error.response.status >= 500;
};

const withElectionFallback = async <T>(request: Promise<BaseResponse<T>>, fallback: () => BaseResponse<T>) => {
  try {
    return await request;
  } catch (error) {
    if (!shouldRecoverWithMock(error)) {
      throw error;
    }

    return fallback();
  }
};

export const getElectionSelector = () =>
  withElectionFallback(
    http.get<ElectionSelectorResponse>({
      url: '/election/selector',
    }),
    () => getMockElectionSelector(),
  );

export const getElectionOverview = (
  electionId: ElectionId,
  regionType: ElectionRegionType,
  regionCode: ElectionRegionCode,
) =>
  withElectionFallback(
    http.get<ElectionOverviewResponse>({
      url: '/election/overview',
      params: { election_id: electionId, region_type: regionType, region_code: regionCode },
    }),
    () => getMockElectionOverview(electionId, regionType, regionCode),
  );

export const getElectionMap = (
  electionId: ElectionId,
  depth: ElectionRegionType,
  regionCode: ElectionRegionCode,
  viewMode: ElectionViewMode,
) =>
  withElectionFallback(
    http.get<ElectionMapResponse>({
      url: '/election/map',
      params: { election_id: electionId, depth, region_code: regionCode, view_mode: viewMode },
    }),
    () => getMockElectionMap(electionId, depth, regionCode, viewMode),
  );

export const getElectionRegionPanel = (
  electionId: ElectionId,
  depth: ElectionRegionType,
  regionCode: ElectionRegionCode,
  officeType?: string | null,
) =>
  withElectionFallback(
    http.get<ElectionRegionPanelResponse>({
      url: '/election/region-panel',
      params: { election_id: electionId, depth, region_code: regionCode, office_type: officeType },
    }),
    () => getMockElectionRegionPanel(electionId, depth, regionCode, officeType),
  );

export const getElectionCandidates = (
  electionId: ElectionId,
  regionCode: ElectionRegionCode,
  officeType?: string | null,
) =>
  withElectionFallback(
    http.get<ElectionCandidateListResponse>({
      url: '/election/candidates',
      params: { election_id: electionId, region_code: regionCode, office_type: officeType },
    }),
    () => getMockElectionCandidates(electionId, regionCode, officeType),
  );

export const getElectionCandidateDetail = (electionId: ElectionId, candidateId: ElectionCandidateId) =>
  withElectionFallback(
    http.get<ElectionCandidateDetailResponse>({
      url: `/election/candidates/${candidateId}`,
      params: { election_id: electionId },
    }),
    () => getMockElectionCandidateDetail(electionId, candidateId),
  );

export const postElectionRegionResolve = (body: ElectionRegionResolveRequest) =>
  withElectionFallback(
    http.post<ElectionRegionResolveResponse>({
      url: '/election/regions/resolve',
      data: body,
    }),
    () => postMockElectionRegionResolve(body),
  );

export const postElectionRegionConfirm = (body: ElectionRegionResolveRequest) =>
  withElectionFallback(
    http.post<ElectionRegionResolveResponse>({
      url: '/election/regions/confirm',
      data: body,
    }),
    () => postMockElectionRegionConfirm(body),
  );
