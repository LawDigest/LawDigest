'use client';

import { motion } from 'framer-motion';
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
            className="relative flex flex-col items-start gap-2 rounded-2xl border border-gray-1 bg-white p-4 text-left shadow-sm transition-colors hover:bg-primary-1 dark:border-dark-l dark:bg-dark-b dark:hover:bg-dark-l">
            {active && (
              // 선택 인디케이터: 분야 고유 색의 얇은 테두리 + 옅은 tint. layoutId로 카드 간 이동 애니메이션.
              <motion.span
                layoutId="explore-category-indicator"
                className="pointer-events-none absolute -inset-px z-0 rounded-2xl"
                style={{ border: `1.5px solid ${meta.color}`, backgroundColor: `${meta.color}14` }}
                transition={{ type: 'spring', stiffness: 350, damping: 30 }}
              />
            )}
            <span className="material-symbols-outlined relative z-10 text-[26px]" style={{ color: meta.color }}>
              {meta.icon}
            </span>
            <span className="relative z-10 text-[15px] font-bold text-primary-3 dark:text-gray-0.5">{meta.label}</span>
            <span className="relative z-10 text-[13px] text-gray-2">관련 법안 {count.toLocaleString()}건</span>
          </button>
        );
      })}
    </div>
  );
}
