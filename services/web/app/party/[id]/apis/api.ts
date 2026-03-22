import { Dispatch, SetStateAction } from 'react';
import http from '@/api';
import { FeedResponse, PartyDetailResponse, ValueOf, PartyCongressmanResponse, PartyFollowResponse } from '@/types';
import { BILL_TAB } from '@/constants';

export const getBillByParty = async (
  partyId: number,
  type: ValueOf<typeof BILL_TAB> | Dispatch<SetStateAction<ValueOf<typeof BILL_TAB>>>,
  page: number,
) =>
  http.get<FeedResponse>({
    url: `/party/bill`,
    params: { party_id: partyId, type, page, size: 3 },
  });

export const getPartyDetail = (partyId: number) =>
  http.get<PartyDetailResponse>({
    url: `/party/detail`,
    params: { party_id: partyId },
  });

export const getPartyCongressman = async (partyId: number) =>
  http.get<PartyCongressmanResponse>({
    url: `/party/congressman`,
    params: { party_id: partyId },
  });

export const patchPartyFollow = (partyId: number, followChecked: boolean) =>
  http.patch<PartyFollowResponse>({
    url: `/party/user/follow`,
    params: { party_id: partyId, follow_checked: followChecked },
  });
