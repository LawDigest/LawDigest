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

export const getBillsByCategory = (category: string, page: number) =>
  http.get<FeedResponse>({
    url: '/bill/category',
    params: { category, page, size: 5 },
  });
