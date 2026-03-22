'use client';

import { QueryClient, useMutation, useSuspenseInfiniteQuery, useQueryClient } from '@tanstack/react-query';
import { BILL_TAB } from '@/constants';
import { ValueOf } from '@/types';
import { Dispatch, SetStateAction } from 'react';
import { getBillByCongressmanId, getCongressmanDetail, patchCongressmanFollow } from './apis';

export const useGetBillByCongressman = (
  id: string,
  type: ValueOf<typeof BILL_TAB> | Dispatch<SetStateAction<ValueOf<typeof BILL_TAB>>>,
) =>
  useSuspenseInfiniteQuery({
    queryKey: ['/congressman/bill_info', id],
    queryFn: ({ pageParam }: { pageParam: number }) => getBillByCongressmanId(pageParam, id, type),
    initialPageParam: 0,
    getNextPageParam: ({ data }) => {
      const { pagination_response } = data || {};
      const { last_page, page_number } = pagination_response || {};
      // eslint-disable-next-line no-nested-ternary
      return last_page ? (page_number === 0 ? 1 : undefined) : page_number + 1;
    },
  });

export const useGetCongressmanDetail = ({
  congressmanId,
  queryClient,
}: {
  congressmanId: string;
  queryClient: QueryClient;
}) =>
  queryClient.fetchQuery({
    queryKey: ['/congressman/detail', congressmanId],
    queryFn: () => getCongressmanDetail(congressmanId),
  });

export const usePatchCongressmanFollow = (congressmanId: string) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (likeChecked: boolean) => patchCongressmanFollow(congressmanId, likeChecked),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['/congressman/detail', congressmanId] });
    },
  });
};
