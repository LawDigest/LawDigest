'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { getCookie } from 'cookies-next';
import { useIntersect } from '@/hooks';
import { ACCESS_TOKEN } from '@/constants';
import { useGetFollowingBill } from '@/app/following/apis';
import { Bill } from '@/components/Bill';
import { Spinner } from '@nextui-org/spinner';

export default function FollowingFeed() {
  const router = useRouter();
  const accessToken = getCookie(ACCESS_TOKEN);
  const { data, hasNextPage, isFetching, fetchNextPage } = useGetFollowingBill();
  const [bills, setBills] = useState(data ? data.pages.flatMap(({ data: { bill_list: responses } }) => responses) : []);

  const fetchRef = useIntersect(async (entry: any, observer: any) => {
    observer.unobserve(entry.target);
    if (hasNextPage && !isFetching) {
      fetchNextPage();
    }
  });

  useEffect(() => {
    if (data) {
      setBills(() => [...data.pages.flatMap(({ data: { bill_list: responses } }) => responses)]);
    }
  }, [data]);

  if (!accessToken) {
    return (
      <div className="flex flex-col items-center justify-center gap-3 py-16 text-center">
        <p className="text-sm text-gray-500">팔로잉 피드를 보려면 로그인이 필요해요.</p>
        <button
          type="button"
          onClick={() => router.push('/login')}
          className="px-4 py-2 text-sm font-medium text-white bg-black rounded-full dark:bg-white dark:text-black">
          로그인하기
        </button>
      </div>
    );
  }

  return (
    <section className="mt-4">
      <ul className="flex flex-col gap-4">
        {bills.map((bill) => (
          <Bill {...bill} key={bill.bill_info_dto.bill_id} />
        ))}
        {bills.length === 0 && !isFetching && (
          <p className="py-12 text-sm text-center text-gray-400">팔로잉한 의원이 없거나 관련 법안이 없어요.</p>
        )}
        {isFetching && (
          <div className="flex justify-center w-full my-4">
            <Spinner color="default" />
          </div>
        )}
        <div ref={fetchRef} />
      </ul>
    </section>
  );
}
