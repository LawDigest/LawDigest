import http from '@/api';
import { FeedResponse, FollowingCongressmanResponse } from '@/types';

export const getFollowingCongressman = () =>
  http.get<FollowingCongressmanResponse>({
    url: '/following-tab/congressman',
  });

export const getFollowingBill = async (page: number) =>
  http.get<FeedResponse>({
    url: '/following-tab/bill',
    params: { page, size: 3 },
  });
