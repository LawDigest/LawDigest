import http from '@/api';

export const postWithdraw = () =>
  http.delete({
    url: `/auth/user/withdraw`,
  });
