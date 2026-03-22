import http from '@/api/config/core';
import { ValueOf, FeedResponse, FeedPopularResponse } from '@/types';
import { STAGE_TAB_KO } from '@/constants';
import { Dispatch, SetStateAction } from 'react';

export const getBillByStage = async (
  page: number,
  stage: ValueOf<'전체' & typeof STAGE_TAB_KO> | Dispatch<SetStateAction<ValueOf<typeof STAGE_TAB_KO>>>,
) =>
  http.get<FeedResponse>({
    url: '/bill/mainfeed',
    params: { page, size: 3, stage },
  });

export const getBillPopular = async () =>
  http.get<FeedPopularResponse>({
    url: `/bill/popular`,
  });
