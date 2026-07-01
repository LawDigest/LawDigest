import http from '@/api';
import { FeedResponse } from '@/types';

export interface CategoryCount {
  category: string;
  count: number;
}

export interface TrendingKeyword {
  keyword: string;
  count: number;
}

export const getCategoryCounts = () => http.get<CategoryCount[]>({ url: '/bill/categories' });

export const getTrendingKeywords = (size = 20) =>
  http.get<TrendingKeyword[]>({ url: '/bill/trending-keywords', params: { size } });

export interface ParliamentaryParty {
  party_id: number;
  party_name: string;
  party_image_url: string;
  congressman_count: number;
}

export const getParliamentaryParties = () => http.get<ParliamentaryParty[]>({ url: '/party/parliamentary' });

export interface CongressmanRanking {
  congressman_id: string;
  congressman_name: string;
  congressman_image_url: string;
  party_id: number;
  party_name: string;
  party_image_url: string;
  propose_count: number;
}

export interface CongressmanListResponse {
  pagination_response: {
    last_page: boolean;
    page_number: number;
  };
  congressman_list: CongressmanRanking[];
}

export const getCongressmanRanking = (size = 3) =>
  http.get<CongressmanRanking[]>({ url: '/congressman/ranking', params: { size } });

export const getCongressmanList = (page: number, partyId?: number | null) =>
  http.get<CongressmanListResponse>({
    url: '/congressman/list',
    params: { page, size: 20, ...(partyId ? { party_id: partyId } : {}) },
  });

export interface StatisticsOverview {
  total_count: number;
  passed_count: number;
  pending_count: number;
  pass_rate: number;
}

export interface StatisticsStage {
  receipt_count: number;
  committee_count: number;
  plenary_count: number;
  promulgated_count: number;
}

export interface PartyBillCount {
  party_id: number;
  party_name: string;
  count: number;
}

export interface MonthlyTrend {
  month: string;
  count: number;
}

export const getStatisticsOverview = () => http.get<StatisticsOverview>({ url: '/statistics/overview' });

export const getStatisticsStage = () => http.get<StatisticsStage>({ url: '/statistics/stage' });

export const getStatisticsByParty = () => http.get<PartyBillCount[]>({ url: '/statistics/by-party' });

export const getStatisticsByCategory = () => http.get<CategoryCount[]>({ url: '/statistics/by-category' });

export const getStatisticsTrend = (months = 6) =>
  http.get<MonthlyTrend[]>({ url: '/statistics/trend', params: { months } });

export const getBillsByCategory = (category: string, page: number) =>
  http.get<FeedResponse>({
    url: '/bill/category',
    params: { category, page, size: 5 },
  });
