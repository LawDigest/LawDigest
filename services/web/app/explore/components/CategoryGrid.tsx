'use client';

import { CSSProperties } from 'react';
import { getCategoryMeta } from '@/config/categories';
import { useGetCategoryCounts } from '../apis';

interface CategoryGridProps {
  selected: string | null;
  onSelect: (code: string) => void;
}

export default function CategoryGrid({ selected, onSelect }: CategoryGridProps) {
  const { data, isLoading } = useGetCategoryCounts();
  const counts = (data?.data ?? []).filter((c) => c.category && c.category !== 'unknown');

  if (isLoading) {
    return <div className="py-10 text-center text-[14px] text-gray-2">분야를 불러오는 중…</div>;
  }

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
      {counts.map(({ category, count }) => {
        const meta = getCategoryMeta(category);
        const active = selected === category;

        return (
          <button
            type="button"
            key={category}
            onClick={() => onSelect(category)}
            aria-pressed={active}
            // 선택 시 해당 분야 고유 색으로 테두리·링 인디케이터를 표시한다.
            style={active ? ({ borderColor: meta.color, '--tw-ring-color': meta.color } as CSSProperties) : undefined}
            className={`flex flex-col items-start gap-2 rounded-2xl border bg-white p-4 text-left shadow-sm transition hover:bg-primary-1 dark:bg-dark-b dark:hover:bg-dark-l ${
              active ? 'ring-2' : 'border-gray-1 dark:border-dark-l'
            }`}>
            <span className="material-symbols-outlined text-[26px]" style={{ color: meta.color }}>
              {meta.icon}
            </span>
            <span className="text-[15px] font-bold text-primary-3 dark:text-gray-0.5">{meta.label}</span>
            <span className="text-[13px] text-gray-2">관련 법안 {count.toLocaleString()}건</span>
          </button>
        );
      })}
    </div>
  );
}
