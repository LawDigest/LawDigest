import { Pagination } from '../common';
import { BillProps } from '../bill';

export interface SearchBillResponse {
  search_response: BillProps;
  pagination_response: Pagination;
}
