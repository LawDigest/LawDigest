'use client';

import { QueryClient, useSuspenseInfiniteQuery, useQuery } from '@tanstack/react-query';
import {
  getUserInfo,
  getFollowingParty,
  getFollowingCongressman,
  getBillBookmarked,
  getBillBookmarkedCount,
} from './apis';

export const useGetUserInfo = (queryClient: QueryClient) =>
  queryClient.fetchQuery({
    queryKey: ['/user/info'],
    queryFn: () => getUserInfo(),
  });

export const useGetFollowingParty = (queryClient: QueryClient) =>
  queryClient.fetchQuery({
    queryKey: ['/user/following/party'],
    queryFn: () => getFollowingParty(),
  });

export const useGetFollowingCongressman = () =>
  useQuery({
    queryKey: ['/user/liking/congressman'],
    queryFn: () => getFollowingCongressman(),
  });

export const useGetBillBookmarked = () =>
  useSuspenseInfiniteQuery({
    queryKey: ['/user/bookmarking/bill'],
    queryFn: ({ pageParam }: { pageParam: number }) => getBillBookmarked(pageParam),
    initialPageParam: 0,
    getNextPageParam: ({ data }) => {
      const { pagination_response } = data || {};
      const { last_page, page_number } = pagination_response || {};
      // eslint-disable-next-line no-nested-ternary
      return last_page ? (page_number === 0 ? 1 : undefined) : page_number + 1;
    },
  });

export const useGetBillBookmarkedCount = () =>
  useQuery({
    queryKey: ['/user/bookmarking/bill/count'],
    queryFn: () => getBillBookmarkedCount(),
  });
