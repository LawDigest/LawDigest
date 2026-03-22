import http from '@/api';
import {
  BillBookmarkedCountResponse,
  FeedResponse,
  FollowingCongressmanResponse,
  FollowingPartyResponse,
  UserInfoResponse,
} from '@/types';

export const getUserInfo = async () =>
  http.get<UserInfoResponse>({
    url: `/user/info`,
  });

export const getFollowingParty = async () =>
  http.get<FollowingPartyResponse>({
    url: `/user/following/party`,
  });

export const getFollowingCongressman = async () =>
  http.get<FollowingCongressmanResponse>({
    url: `/user/liking/congressman`,
  });

export const postLogout = async () =>
  http.post({
    url: `/logout`,
  });

export const getBillBookmarked = async (page: number) =>
  http.get<FeedResponse>({
    url: `/user/bookmarking/bill`,
    params: { page, size: 3 },
  });

export const getBillBookmarkedCount = async () =>
  http.get<BillBookmarkedCountResponse>({
    url: `/user/bookmarking/bill/count`,
  });
