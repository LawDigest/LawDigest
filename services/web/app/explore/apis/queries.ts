'use client';

import { useQuery, useSuspenseInfiniteQuery } from '@tanstack/react-query';
import { getBillsByCategory, getCategoryCounts } from './apis';

export const useGetCategoryCounts = () =>
  useQuery({
    queryKey: ['/bill/categories'],
    queryFn: () => getCategoryCounts(),
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
