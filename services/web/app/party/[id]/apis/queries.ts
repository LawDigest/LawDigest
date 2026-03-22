'use client';

import { useSuspenseInfiniteQuery, QueryClient, useQueryClient, useMutation, useQuery } from '@tanstack/react-query';
import { Dispatch, SetStateAction } from 'react';
import { BILL_TAB } from '@/constants';
import { ValueOf } from '@/types';
import { getBillByParty, getPartyDetail, getPartyCongressman, patchPartyFollow } from './api';

export const useGetBillByParty = (
  id: number,
  type: ValueOf<typeof BILL_TAB> | Dispatch<SetStateAction<ValueOf<typeof BILL_TAB>>>,
) =>
  useSuspenseInfiniteQuery({
    queryKey: ['/party/bill', id],
    queryFn: ({ pageParam }: { pageParam: number }) => getBillByParty(id, type, pageParam),
    initialPageParam: 0,
    getNextPageParam: ({ data }) => {
      const { pagination_response } = data || {};
      const { last_page, page_number } = pagination_response || {};
      // eslint-disable-next-line no-nested-ternary
      return last_page ? (page_number === 0 ? 1 : undefined) : page_number + 1;
    },
  });

export const useGetPartyDetail = ({ partyId, queryClient }: { partyId: number; queryClient: QueryClient }) =>
  queryClient.fetchQuery({
    queryKey: ['/party/detail', partyId],
    queryFn: () => getPartyDetail(partyId),
  });

export const useGetPartyCongressman = (partyId: number) =>
  useQuery({
    queryKey: ['/party/congressman', { party_id: partyId }],
    queryFn: () => getPartyCongressman(partyId),
  });

export const usePatchPartyFollow = (partyId: number) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (followChecked: boolean) => patchPartyFollow(partyId, followChecked),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['/party/detail', partyId] });
    },
  });
};
