'use client';

import { useQuery, useSuspenseInfiniteQuery } from '@tanstack/react-query';
import {
  getBillsByCategory,
  getCategoryCounts,
  getCongressmanList,
  getCongressmanRanking,
  getParliamentaryParties,
  getStatisticsByCategory,
  getStatisticsByCommittee,
  getStatisticsByParty,
  getStatisticsCategoryParty,
  getStatisticsOverview,
  getStatisticsPartyPerformance,
  getStatisticsResultBreakdown,
  getStatisticsStage,
  getStatisticsTrend,
  getStatisticsTrendDetail,
  getTrendingKeywords,
} from './apis';

export const useGetCategoryCounts = () =>
  useQuery({
    queryKey: ['/bill/categories'],
    queryFn: () => getCategoryCounts(),
  });

export const useGetTrendingKeywords = (size = 20) =>
  useQuery({
    queryKey: ['/bill/trending-keywords', size],
    queryFn: () => getTrendingKeywords(size),
  });

export const useGetParliamentaryParties = () =>
  useQuery({
    queryKey: ['/party/parliamentary'],
    queryFn: () => getParliamentaryParties(),
  });

export const useGetCongressmanRanking = (size = 3) =>
  useQuery({
    queryKey: ['/congressman/ranking', size],
    queryFn: () => getCongressmanRanking(size),
  });

export const useGetCongressmanList = (partyId?: number | null) =>
  useSuspenseInfiniteQuery({
    queryKey: ['/congressman/list', partyId ?? 'all'],
    queryFn: ({ pageParam }: { pageParam: number }) => getCongressmanList(pageParam, partyId),
    initialPageParam: 0,
    getNextPageParam: ({ data }) => {
      const { pagination_response } = data || {};
      const { last_page, page_number } = pagination_response || {};
      return last_page ? undefined : page_number + 1;
    },
  });

export const useGetStatisticsOverview = () =>
  useQuery({ queryKey: ['/statistics/overview'], queryFn: () => getStatisticsOverview() });

export const useGetStatisticsStage = () =>
  useQuery({ queryKey: ['/statistics/stage'], queryFn: () => getStatisticsStage() });

export const useGetStatisticsByParty = () =>
  useQuery({ queryKey: ['/statistics/by-party'], queryFn: () => getStatisticsByParty() });

export const useGetStatisticsByCategory = () =>
  useQuery({ queryKey: ['/statistics/by-category'], queryFn: () => getStatisticsByCategory() });

export const useGetStatisticsTrend = (months = 6) =>
  useQuery({ queryKey: ['/statistics/trend', months], queryFn: () => getStatisticsTrend(months) });

// 신규 통계 API — 배포 전 백엔드에는 없을 수 있어 재시도 없이 실패시키고, 컴포넌트에서 폴백 처리한다.
export const useGetStatisticsPartyPerformance = () =>
  useQuery({
    queryKey: ['/statistics/party-performance'],
    queryFn: () => getStatisticsPartyPerformance(),
    retry: false,
  });

export const useGetStatisticsTrendDetail = (months = 12) =>
  useQuery({
    queryKey: ['/statistics/trend-detail', months],
    queryFn: () => getStatisticsTrendDetail(months),
    retry: false,
  });

export const useGetStatisticsByCommittee = () =>
  useQuery({
    queryKey: ['/statistics/by-committee'],
    queryFn: () => getStatisticsByCommittee(),
    retry: false,
  });

export const useGetStatisticsCategoryParty = () =>
  useQuery({
    queryKey: ['/statistics/category-party'],
    queryFn: () => getStatisticsCategoryParty(),
    retry: false,
  });

export const useGetStatisticsResultBreakdown = () =>
  useQuery({
    queryKey: ['/statistics/result-breakdown'],
    queryFn: () => getStatisticsResultBreakdown(),
    retry: false,
  });

export const useGetBillsByCategory = (category: string) =>
  useSuspenseInfiniteQuery({
    queryKey: ['/bill/category', category],
    queryFn: ({ pageParam }: { pageParam: number }) => getBillsByCategory(category, pageParam),
    initialPageParam: 0,
    getNextPageParam: ({ data }) => {
      const { pagination_response } = data || {};
      const { last_page, page_number } = pagination_response || {};
      return last_page ? undefined : page_number + 1;
    },
  });
