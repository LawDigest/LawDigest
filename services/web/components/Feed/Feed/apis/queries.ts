'use client';

import { useSuspenseInfiniteQuery, useQuery } from '@tanstack/react-query';
import { STAGE_TAB_KO } from '@/constants';
import { ValueOf } from '@/types';
import { Dispatch, SetStateAction } from 'react';
import { getBillByStage, getBillPopular } from './apis';

export const useGetBillByStage = (
  stage: ValueOf<'전체' & typeof STAGE_TAB_KO> | Dispatch<SetStateAction<ValueOf<'전체' & typeof STAGE_TAB_KO>>>,
) =>
  useSuspenseInfiniteQuery({
    queryKey: ['/bill/mainfeed'],
    queryFn: ({ pageParam }: { pageParam: number }) => getBillByStage(pageParam, stage),
    initialPageParam: 0,
    getNextPageParam: ({ data }) => {
      const { pagination_response } = data || {};
      const { last_page, page_number } = pagination_response || {};
      return last_page ? undefined : page_number + 1;
    },
  });

export const useGetBillPopular = () =>
  useQuery({
    queryKey: ['/bill/popular'],
    queryFn: () => getBillPopular(),
  });
