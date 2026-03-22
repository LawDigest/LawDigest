'use clinet';

import { useMutation, useQueryClient, QueryClient } from '@tanstack/react-query';
import { getBillDetail, patchViewCount, postBookmark } from './apis';

export const useGetBillDetail = (billId: string, queryClient: QueryClient) =>
  queryClient.fetchQuery({
    queryKey: ['/bill/detail', billId],
    queryFn: () => getBillDetail(billId),
  });

export const usePatchViewCount = async (billId: string) => {
  const response = await patchViewCount(billId);

  return response;
};

export const usePatchBookmark = (billId: string) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (likeChecked: boolean) => postBookmark(billId, likeChecked),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['/bill/detail', billId] });
      queryClient.invalidateQueries({ queryKey: ['/bill/mainfeed'] });
      queryClient.invalidateQueries({ queryKey: ['/user/bookmarking/bill'] });
      queryClient.invalidateQueries({ queryKey: ['/user/bookmarking/bill/count'] });
    },
  });
};
