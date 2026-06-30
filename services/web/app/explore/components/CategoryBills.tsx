'use client';

import { useEffect, useState } from 'react';
import { Spinner } from '@nextui-org/spinner';
import { Bill } from '@/components';
import { useIntersect } from '@/hooks';
import { BillProps } from '@/types';
import { useGetBillsByCategory } from '../apis';

export default function CategoryBills({ category }: { category: string }) {
  const { data, hasNextPage, isFetching, fetchNextPage } = useGetBillsByCategory(category);
  const [bills, setBills] = useState<BillProps[]>(
    data ? data.pages.flatMap(({ data: { bill_list } }) => bill_list) : [],
  );

  const fetchRef = useIntersect(async (entry: IntersectionObserverEntry, observer: IntersectionObserver) => {
    observer.unobserve(entry.target);
    if (hasNextPage && !isFetching) {
      fetchNextPage();
    }
  });

  useEffect(() => {
    if (data) {
      setBills([...data.pages.flatMap(({ data: { bill_list } }) => bill_list)]);
    }
  }, [data]);

  if (bills.length === 0 && !isFetching) {
    return <div className="py-10 text-center text-[14px] text-gray-2">해당 분야의 법안이 없습니다.</div>;
  }

  return (
    <section className="flex flex-col gap-6">
      {bills.map((bill) => (
        <Bill {...bill} key={bill.bill_info_dto.bill_id} />
      ))}
      {isFetching && (
        <div className="flex justify-center py-4">
          <Spinner color="default" />
        </div>
      )}
      <div ref={fetchRef} />
    </section>
  );
}
