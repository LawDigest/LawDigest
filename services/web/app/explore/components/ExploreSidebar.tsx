'use client';

import { EXPLORE_TABS, ExploreTab } from './tabs';

interface ExploreSidebarProps {
  active: ExploreTab;
  onChange: (tab: ExploreTab) => void;
}

/** 데스크톱(lg+) 좌측 사이드바 (분야/국회/통계). 모바일에서는 서브탭 바로 대체된다. */
export default function ExploreSidebar({ active, onChange }: ExploreSidebarProps) {
  return (
    <aside className="hidden shrink-0 lg:block lg:w-[200px]">
      <div className="sticky top-[112px]">
        <p className="mb-2 px-3 text-[12px] font-semibold uppercase tracking-wide text-gray-2">탐색</p>
        <nav className="flex flex-col gap-1" aria-label="탐색 하위 탭">
          {EXPLORE_TABS.map(({ key, label, icon }) => {
            const isActive = key === active;
            return (
              <button
                key={key}
                type="button"
                aria-current={isActive ? 'page' : undefined}
                onClick={() => onChange(key)}
                className={[
                  'flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-[14px] font-semibold transition-colors',
                  isActive
                    ? 'bg-primary-1 text-primary-3 dark:bg-dark-l dark:text-gray-0.5'
                    : 'text-gray-3 hover:bg-gray-0.5 dark:text-gray-1 dark:hover:bg-dark-l',
                ].join(' ')}>
                <span className="material-symbols-outlined text-[22px]">{icon}</span>
                {label}
              </button>
            );
          })}
        </nav>
      </div>
    </aside>
  );
}
