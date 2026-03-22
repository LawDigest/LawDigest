import http from '@/api';
import { BillResponse, ViewCountResponse, BookmarkResponse } from '@/types';

export const getBillDetail = async (billId: string) =>
  http.get<BillResponse>({
    url: `/bill/detail/${billId}`,
  });

export const patchViewCount = (billId: string) =>
  http.patch<ViewCountResponse>({
    url: `/bill/view_count`,
    params: { bill_id: billId },
  });

export const postBookmark = (billId: string, likeChecked: boolean) =>
  http.patch<BookmarkResponse>({
    url: `/bill/user/bookmark`,
    params: { bill_id: billId, likeChecked },
  });
