import http from '@/api';
import { SearchCongressmanPartyResponse, SearchBillResponse } from '@/types';

export const getSearchCongressmanParty = async (searchWord: string) =>
  http.get<SearchCongressmanPartyResponse>({
    url: `/search/congressman/party`,
    params: { search_word: searchWord },
  });

export const getSearchBill = async (searchWord: string, page: number) =>
  http.get<SearchBillResponse>({
    url: `/search/bill`,
    params: { search_word: searchWord, page },
  });
