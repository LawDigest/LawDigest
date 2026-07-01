'use client';

import { Suspense, useState } from 'react';
import { getCategoryMeta } from '@/config/categories';
import TrendingKeywords from './TrendingKeywords';
import CategoryGrid from './CategoryGrid';
import CategoryBills from './CategoryBills';

export default function FieldPanel() {
  const [selected, setSelected] = useState<string | null>(null);

  return (
    <div className="flex flex-col gap-7">
      <TrendingKeywords />

      <section className="flex flex-col gap-3">
        <h2 className="text-[15px] font-bold text-primary-3 dark:text-gray-0.5">분야별 둘러보기</h2>
        <CategoryGrid selected={selected} onSelect={setSelected} />
      </section>

      {selected && (
        <section className="flex flex-col gap-4">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-[22px]" style={{ color: getCategoryMeta(selected).color }}>
              {getCategoryMeta(selected).icon}
            </span>
            <h2 className="text-[17px] font-bold text-primary-3 dark:text-gray-0.5">
              {getCategoryMeta(selected).label} 관심 법안
            </h2>
          </div>
          <Suspense fallback={<div className="py-10 text-center text-[14px] text-gray-2">법안을 불러오는 중…</div>}>
            <CategoryBills key={selected} category={selected} />
          </Suspense>
        </section>
      )}
    </div>
  );
}
