'use client';

import Link from 'next/link';
import { useGetTrendingKeywords } from '../apis';

/**
 * 지금 뜨는 키워드 — 법안 요약 태그(summary_tags) 상위 N개.
 * 운영 데이터가 아직 없을 수 있으므로, 키워드가 없으면 섹션 전체를 숨긴다.
 */
export default function TrendingKeywords() {
  const { data } = useGetTrendingKeywords(12);
  const keywords = data?.data ?? [];

  if (keywords.length === 0) return null;

  return (
    <section className="flex flex-col gap-3">
      <div className="flex items-center gap-1.5">
        <span className="material-symbols-outlined text-[20px] text-theme-alert">local_fire_department</span>
        <h2 className="text-[15px] font-bold text-primary-3 dark:text-gray-0.5">지금 뜨는 키워드</h2>
      </div>
      <div className="-mx-4 flex gap-2 overflow-x-auto px-4 scrollbar-hide md:mx-0 md:flex-wrap md:overflow-visible md:px-0">
        {keywords.map(({ keyword, count }) => (
          <Link
            key={keyword}
            href={`/search/${encodeURIComponent(keyword)}`}
            className="shrink-0 rounded-full border border-gray-1 bg-white px-3.5 py-2 text-[13px] font-medium text-primary-3 shadow-sm transition-colors hover:bg-primary-1 dark:border-dark-l dark:bg-dark-b dark:text-gray-0.5 dark:hover:bg-dark-l">
            <span style={{ color: '#0088FF' }}>#</span> {keyword}
            <span className="ml-1 text-gray-2">{count.toLocaleString()}</span>
          </Link>
        ))}
      </div>
    </section>
  );
}
