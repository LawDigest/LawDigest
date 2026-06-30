'use client';

import { Suspense, useState } from 'react';
import { getCategoryMeta } from '@/config/categories';
import CategoryGrid from './CategoryGrid';
import CategoryBills from './CategoryBills';

export default function ExploreBoard() {
  const [selected, setSelected] = useState<string | null>(null);

  return (
    <section className="flex w-full flex-col gap-6 px-4 py-5">
      <header className="flex flex-col gap-1">
        <h1 className="text-[20px] font-bold text-primary-3">분야별 탐색</h1>
        <p className="text-[14px] text-gray-2">관심 있는 생활 분야를 골라 관련 법안을 살펴보세요.</p>
      </header>

      <CategoryGrid selected={selected} onSelect={setSelected} />

      {selected && (
        <section className="flex flex-col gap-4">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-[22px] text-primary-3">
              {getCategoryMeta(selected).icon}
            </span>
            <h2 className="text-[17px] font-bold text-primary-3">{getCategoryMeta(selected).label}</h2>
          </div>
          <Suspense fallback={<div className="py-10 text-center text-[14px] text-gray-2">법안을 불러오는 중…</div>}>
            <CategoryBills key={selected} category={selected} />
          </Suspense>
        </section>
      )}
    </section>
  );
}
