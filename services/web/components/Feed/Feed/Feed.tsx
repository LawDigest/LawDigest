'use client';

import { useEffect, useState, useMemo } from 'react';
import { useIntersect, useTabType } from '@/hooks';
import { BillList } from '@/components/Bill';
import { FEED_TAB } from '@/constants';
import { useGetBillByStage, useGetBillPopular } from './apis';
import StageDropdown from '../StageDropdown';
import FeedTab from '../FeedTab';

export default function Feed() {
  const [feedType, setFeedType] = useTabType<typeof FEED_TAB>('sorted_by_latest');
  const [stageType, setStageType] = useState(new Set(['전체']));
  const selectedStageType = useMemo(() => Array.from(stageType).join(', ').replaceAll('_', ' '), [stageType]);
  const { data, hasNextPage, isFetching, fetchNextPage, refetch } = useGetBillByStage(
    selectedStageType === '전체' ? '' : selectedStageType,
  );
  const [bills, setBills] = useState(
    data ? data.pages.flatMap(({ data: { bill_list: responses } }) => responses || []) : [],
  );
  const { data: popularFeed } = useGetBillPopular();
  const [popularBills, setPopularBills] = useState(popularFeed?.data || []);

  const fetchRef = useIntersect(async (entry: any, observer: any) => {
    observer.unobserve(entry.target);
    if (hasNextPage && !isFetching) {
      fetchNextPage();
    }
  });

  useEffect(() => {
    if (data) {
      setBills(() => [...data.pages.flatMap(({ data: { bill_list: responses } }) => responses || [])]);
    }
  }, [data]);

  useEffect(() => {
    if (popularFeed) {
      setPopularBills(() => (popularFeed.data ? [...popularFeed.data] : []));
    }
  }, [popularFeed]);

  useEffect(() => {
    setBills([]);
    refetch();
  }, [selectedStageType]);

  return (
    <section>
      <section className="flex items-center justify-between mx-5 mt-5">
        <FeedTab type={feedType as any} clickHandler={setFeedType as any} />
        {feedType === 'sorted_by_latest' && (
          <StageDropdown type={selectedStageType as any} clickHandler={setStageType as any} />
        )}
      </section>
      <BillList
        bills={feedType === 'sorted_by_latest' ? bills : popularBills}
        isFetching={isFetching}
        fetchRef={fetchRef}
        feedType={feedType as any}
      />
    </section>
  );
}
