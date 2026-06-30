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
      {counts.map(({ category, count }) => {
        const meta = getCategoryMeta(category);
        const active = selected === category;
        return (
          <button
            type="button"
            key={category}
            onClick={() => onSelect(category)}
            aria-pressed={active}
            className={`flex flex-col items-start gap-2 rounded-2xl border p-4 text-left transition ${
              active ? 'border-primary-2 bg-primary-1' : 'border-gray-1 bg-white hover:bg-primary-1'
            }`}
          >
            <span className="material-symbols-outlined text-[26px] text-primary-3">{meta.icon}</span>
            <span className="text-[15px] font-bold text-primary-3">{meta.label}</span>
            <span className="text-[13px] text-gray-2">{count.toLocaleString()}건</span>
          </button>
        );
      })}
    </div>
  );
}
