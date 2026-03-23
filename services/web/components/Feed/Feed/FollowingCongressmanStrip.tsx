'use client';

import { useQuery } from '@tanstack/react-query';
import { getCookie } from 'cookies-next';
import { Card, CardHeader, CardBody } from '@nextui-org/react';
import { ACCESS_TOKEN } from '@/constants';
import { getFollowingCongressman } from '@/app/following/apis';
import CongressmanList from '@/app/following/components/FollowingHeader/CongressmanList';

export default function FollowingCongressmanStrip() {
  const accessToken = getCookie(ACCESS_TOKEN);
  const { data } = useQuery({
    queryKey: ['/following-tab/congressman'],
    queryFn: getFollowingCongressman,
    enabled: Boolean(accessToken),
  });

  const congressmanList = data?.data;
  if (!accessToken || !congressmanList) return null;

  return (
    <Card
      classNames={{
        base: ['shadow-[0_4px_6px_-2px_rgba(0,_0,_0,_0.1)] md:shadow-[0_0_6px_rgba(0,_0,_0,_0.1)]'],
      }}
      className="w-full pl-5 mx-auto bg-transparent md:mt-10 md:mb-6 md:h-[200px] md:w-[708px] md:pt-3 md:rounded-xl md:dark:bg-primary-3 md:border border-b dark:border-dark-l">
      <CardHeader className="pt-2 pb-0 pl-0">
        <h2 className="text-2xl font-bold md:text-3xl">팔로잉</h2>
      </CardHeader>
      <CardBody className="flex flex-row items-center gap-4 pl-0 overflow-x-scroll scrollbar-hide">
        <div className="flex flex-col items-center shrink-0">
          <p className="text-xs font-medium text-gray-2 md:text-sm">팔로우한 의원</p>
          <p className="text-2xl font-semibold">{congressmanList.length}</p>
        </div>
        <CongressmanList congressmanList={congressmanList} />
      </CardBody>
    </Card>
  );
}
