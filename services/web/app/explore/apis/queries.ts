'use client';

import { useQuery, useSuspenseInfiniteQuery } from '@tanstack/react-query';
import {
  getBillsByCategory,
  getCategoryCounts,
  getCongressmanList,
  getCongressmanRanking,
  getParliamentaryParties,
  getStatisticsByCategory,
  getStatisticsByParty,
  getStatisticsOverview,
  getStatisticsStage,
  getStatisticsTrend,
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
