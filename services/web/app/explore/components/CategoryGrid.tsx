'use client';

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
      {counts.map(({ category, count }, index) => {
        const meta = getCategoryMeta(category);
        const active = selected === category;
        // 건수 1위 분야는 HOT 다크 카드로 강조한다.
        const isHot = index === 0;

        if (isHot) {
          return (
            <button
              type="button"
              key={category}
              onClick={() => onSelect(category)}
              aria-pressed={active}
              className={`relative flex flex-col items-start gap-2 overflow-hidden rounded-2xl bg-primary-3 p-4 text-left text-white shadow-sm transition ${
                active ? 'ring-2 ring-primary-2' : ''
              }`}>
              <span className="absolute right-3 top-3 rounded-full bg-theme-info px-2 py-0.5 text-[10px] font-bold text-primary-3">
                HOT
              </span>
              <span className="material-symbols-outlined text-[26px]">{meta.icon}</span>
              <span className="text-[15px] font-bold">{meta.label}</span>
              <span className="text-[13px] text-white/70">관련 법안 {count.toLocaleString()}건</span>
            </button>
          );
        }

        return (
          <button
            type="button"
            key={category}
            onClick={() => onSelect(category)}
            aria-pressed={active}
            className={`flex flex-col items-start gap-2 rounded-2xl border bg-white p-4 text-left shadow-sm transition hover:bg-primary-1 dark:bg-dark-b dark:hover:bg-dark-l ${
              active ? 'border-primary-2 ring-1 ring-primary-2' : 'border-gray-1 dark:border-dark-l'
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
