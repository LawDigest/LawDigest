'use client';

import { useState, useEffect } from 'react';
import Image from 'next/image';
import { useIntersect } from '@/hooks';
import { Card } from '@nextui-org/card';
import { useGetBillBookmarked } from '../../apis';
import BillBookmarkedCount from './BillBookmarkedCount';
import BillBookmarkedList from './BillBookmaredList';

export default function BillContainer() {
  const { data, hasNextPage, isFetching, fetchNextPage } = useGetBillBookmarked();
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

  return (
    <section className="lg:px-[30px] flex flex-col gap-6">
      <p className="text-xl font-semibold px-[30px] lg:px-0">
        스크랩한 법안 &middot; <BillBookmarkedCount />
      </p>
      <Card className="mx-[30px] lg:mx-0 bg-primary-3 dark:lg:bg-dark-b rounded-lg px-6 py-5 flex-row gap-8 items-center">
        <Image
          src="/images/scrab.png"
          width={64}
          height={64}
          alt="스크랩 아이콘 이미지"
          priority
          loader={({ src }) => `${src}`}
          className="shrink-0"
        />
        <p className="text-base font-semibold text-white lg:text-lg">이곳에서 스크랩한 법안들을 모아서 확인하세요!</p>
      </Card>
      <BillBookmarkedList bills={bills} isFetching={isFetching} fetchRef={fetchRef} />
    </section>
  );
}
