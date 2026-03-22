'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { getCookie } from 'cookies-next';
import { ACCESS_TOKEN } from '@/constants';
import { dehydrate, HydrationBoundary, useQueryClient } from '@tanstack/react-query';
import { useSetRecoilState } from 'recoil';
import { snackbarState } from '@/store';
import { CongressmanList, UserInfo, PartyList, BillContainer } from './components';

export default function MyPage() {
  const router = useRouter();
  const accessToken = getCookie(ACCESS_TOKEN);
  const queryClient = useQueryClient();
  const setSnackbar = useSetRecoilState(snackbarState);

  useEffect(() => {
    if (!accessToken) {
      setSnackbar({ show: true, type: 'ERROR', message: '로그인이 필요한 서비스입니다.', duration: 3000 });
      router.push('/login');
    }
  }, [setSnackbar]);

  if (!accessToken)
    return <div className="flex items-center justify-center h-full [140px] md:mt-[180px]">회원 정보가 없습니다.</div>;

  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      <div className="flex flex-col h-full gap-8 lg:flex-row md:items-center lg:items-start lg:justify-center lg:mt-10 lg:mx-auto lg:ml-10 xl:ml-0">
        <UserInfo queryClient={queryClient} />
        <div className="flex flex-col h-full gap-8">
          <PartyList qeuryClient={queryClient} />
          <hr className="mx-[30px] border-[#E0E0E0] dark:border-dark-l lg:border-transparent dark:lg:border-transparent" />
          <CongressmanList />
          <hr className="mx-[30px] border-[#E0E0E0] dark:border-dark-l lg:border-transparent dark:lg:border-transparent" />
          <BillContainer />
        </div>
      </div>
    </HydrationBoundary>
  );
}
