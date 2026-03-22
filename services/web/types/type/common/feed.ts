import { BillProps } from '../bill/bill';
import { Pagination } from './pagination';

export interface FeedResponse {
  bill_list: BillProps;
  pagination_response: Pagination;
}

export type FeedPopularResponse = BillProps[];
