'use client';

import { useEffect, useState, useMemo } from 'react';
import { useIntersect, useTabType } from '@/hooks';
import { BillList } from '@/components/Bill';
import { FEED_TAB } from '@/constants';
import { NotificationTopThree } from '@/app/notification/components';
import { useGetBillByStage, useGetBillPopular } from './apis';
import StageDropdown from '../StageDropdown';
import FeedTab from '../FeedTab';
import FollowingFeed from './FollowingFeed';
import FollowingCongressmanStrip from './FollowingCongressmanStrip';

type ContentType = 'report' | 'bill' | 'following';

const CONTENT_TABS: { label: string; value: ContentType; icon: React.ReactNode }[] = [
  {
    label: '리포트',
    value: 'report',
    icon: (
      <svg width="16" height="16" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path
          d="M4 3.5C4 2.672 4.672 2 5.5 2H12L16 6V16.5C16 17.328 15.328 18 14.5 18H5.5C4.672 18 4 17.328 4 16.5V3.5Z"
          stroke="currentColor"
          strokeWidth="1.4"
          strokeLinejoin="round"
        />
        <path d="M12 2V6H16" stroke="currentColor" strokeWidth="1.4" strokeLinejoin="round" />
        <path d="M7 10H13M7 13H11" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
        <circle cx="15" cy="5" r="3" fill="currentColor" />
        <path d="M14 5L14.7 5.7L16.3 4" stroke="white" strokeWidth="1.1" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
  },
  {
    label: '법안',
    value: 'bill',
    icon: (
      <svg width="16" height="16" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M4 5.5H16" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        <path d="M4 9.5H16" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        <path d="M4 13.5H12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
      </svg>
    ),
  },
  {
    label: '팔로잉',
    value: 'following',
    icon: (
      <svg width="16" height="16" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path
          d="M4 17V3H16V17L10.5 14.2L10 13.95L9.5 14.2L4 17Z"
          stroke="currentColor"
          strokeWidth="1.4"
          strokeLinejoin="round"
        />
      </svg>
    ),
  },
];

export default function Feed() {
  const [contentType, setContentType] = useState<ContentType>('report');
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
      {/* 피드 헤더: 제목 */}
      <div className="mx-5 mt-5 mb-3">
        <h2 className="text-[26px] font-bold leading-tight text-black dark:text-white">피드</h2>
      </div>

      {/* 콘텐츠 타입 탭 - 슬라이딩 인디케이터 */}
      <div className="relative flex items-center gap-[5px] mx-6 mb-3">
        {/* 슬라이딩 인디케이터 */}
        <div
          className="feed-tab-indicator"
          style={{
            transform: `translateX(${CONTENT_TABS.findIndex((t) => t.value === contentType) * (85 + 5)}px)`,
          }}
        />
        {CONTENT_TABS.map(({ label, value, icon }) => (
          <button
            key={value}
            type="button"
            onClick={() => setContentType(value)}
            className={`feed-content-tab${contentType === value ? ' is-active' : ''}`}>
            {icon}
            <span>{label}</span>
          </button>
        ))}
      </div>

      {/* 알림 카드 — 팔로잉 탭에서는 숨김 */}
      {contentType !== 'following' && <NotificationTopThree />}

      {/* 리포트 탭 */}
      {contentType === 'report' && (
        <>
          <section className="flex items-center justify-between mx-5 mt-2">
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
        </>
      )}

      {/* 법안 탭 */}
      {contentType === 'bill' && (
        <>
          <section className="flex items-center justify-between mx-5 mt-2">
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
        </>
      )}

      {/* 팔로잉 탭 */}
      {contentType === 'following' && (
        <>
          <FollowingCongressmanStrip />
          <FollowingFeed />
        </>
      )}
    </section>
  );
}
