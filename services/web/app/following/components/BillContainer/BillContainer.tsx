'use client';

import { useState, useEffect } from 'react';
import { useIntersect } from '@/hooks';
import { useGetFollowingBill } from '../../apis';
import BillFollowedList from './BillFollowedList';

export default function BillContainer() {
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

  return (
    <section className="flex flex-col gap-6">
      <BillFollowedList bills={bills} isFetching={isFetching} fetchRef={fetchRef} />
    </section>
  );
}
