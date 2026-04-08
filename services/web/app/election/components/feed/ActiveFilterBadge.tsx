'use client';

interface ActiveFilterBadgeProps {
  label: string;
  onClear: () => void;
}

export default function ActiveFilterBadge({ label, onClear }: ActiveFilterBadgeProps) {
  return (
    <div className="flex items-center justify-between px-4 py-2 bg-blue-50 dark:bg-dark-l/40 border-b border-gray-200 dark:border-dark-l text-xs text-gray-600 dark:text-gray-300">
      <span className="flex items-center gap-1.5">
        <span className="material-symbols-outlined text-[14px] text-blue-500">filter_alt</span>
        <span className="font-medium">{label} 필터 적용 중</span>
      </span>
      <button
        type="button"
        onClick={onClear}
        aria-label="필터 해제"
        className="flex items-center gap-0.5 text-gray-400 hover:text-gray-600 dark:hover:text-white transition-colors">
        <span className="material-symbols-outlined text-[14px]">close</span>
        해제
      </button>
    </div>
  );
}
