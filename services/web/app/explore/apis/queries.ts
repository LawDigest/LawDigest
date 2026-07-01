'use client';

import { useQuery, useSuspenseInfiniteQuery } from '@tanstack/react-query';
import {
  getBillsByCategory,
  getCategoryCounts,
  getCongressmanList,
  getCongressmanRanking,
  getParliamentaryParties,
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
