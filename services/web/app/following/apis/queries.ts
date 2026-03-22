import { QueryClient, useInfiniteQuery } from '@tanstack/react-query';
import { getFollowingBill, getFollowingCongressman } from './apis';

export const useGetFollowingCongressman = (queryClient: QueryClient) =>
  queryClient.fetchQuery({
    queryKey: ['/following-tab/congressman'],
    queryFn: () => getFollowingCongressman(),
  });

export const useGetFollowingBill = () =>
  useInfiniteQuery({
    queryKey: ['/following-tab/bill'],
    queryFn: ({ pageParam }: { pageParam: number }) => getFollowingBill(pageParam),
    initialPageParam: 0,
    getNextPageParam: ({ data }) => {
      const { pagination_response } = data || {};
      const { last_page, page_number } = pagination_response || {};
      return last_page ? undefined : page_number + 1;
    },
  });
