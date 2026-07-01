'use client';

import { EXPLORE_TABS, ExploreTab } from './tabs';

interface ExploreSubTabsProps {
  active: ExploreTab;
  onChange: (tab: ExploreTab) => void;
}

/** 모바일·태블릿용 밑줄형 서브탭 (분야/국회/통계). 데스크톱(lg+)에서는 사이드바로 대체된다. */
export default function ExploreSubTabs({ active, onChange }: ExploreSubTabsProps) {
  return (
    <div
      role="tablist"
      aria-label="탐색 하위 탭"
      className="sticky top-[56px] z-20 flex overflow-x-auto border-b border-divider bg-white px-2 backdrop-blur dark:border-dark-l dark:bg-dark-b scrollbar-hide lg:hidden">
      {EXPLORE_TABS.map(({ key, label }) => {
        const isActive = key === active;
        return (
          <button
            key={key}
            type="button"
            role="tab"
            aria-selected={isActive}
            onClick={() => onChange(key)}
            className={[
              'relative min-w-[72px] flex-1 h-11 px-2 text-[15px] font-semibold transition-colors whitespace-nowrap',
              isActive ? 'text-primary-3 dark:text-gray-0.5' : 'text-gray-2 hover:text-gray-3 dark:hover:text-gray-1',
            ].join(' ')}>
            {label}
            {isActive && (
              <span
                aria-hidden="true"
                className="absolute bottom-0 left-0 h-[2.5px] w-full rounded-full bg-primary-3 dark:bg-gray-0.5"
              />
            )}
          </button>
        );
      })}
    </div>
  );
}
