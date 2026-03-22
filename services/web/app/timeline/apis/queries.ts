'use client';

import { useQuery, useSuspenseInfiniteQuery } from '@tanstack/react-query';
import { getTimelineFeed, getTimelineBillState } from './apis';

export const useGetTimelineFeed = () =>
  useSuspenseInfiniteQuery({
    queryKey: ['/time-line/feed/paging'],
    queryFn: ({ pageParam }: { pageParam: number }) => getTimelineFeed(pageParam),
    initialPageParam: 0,
    getNextPageParam: ({ data }) => {
      const { pagination_response } = data || {};
      const { last_page, page_number } = pagination_response || {};
      return last_page ? undefined : page_number + 1;
    },
  });

export const useGetTimelineBillState = () =>
  useQuery({
    queryKey: ['/time-line/bill-state'],
    queryFn: () => getTimelineBillState(),
  });
