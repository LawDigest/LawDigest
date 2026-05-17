'use client';

export type ElectionInnerTab = 'map' | 'feed' | 'poll' | 'district';

interface Tab {
  key: ElectionInnerTab;
  label: string;
}

const TABS: Tab[] = [
  { key: 'map', label: '지도' },
  { key: 'feed', label: '피드' },
  { key: 'poll', label: '여론조사' },
  { key: 'district', label: '내 지역구' },
];

interface ElectionInnerTabBarProps {
  activeTab: ElectionInnerTab;
  onChange: (tab: ElectionInnerTab) => void;
}

export default function ElectionInnerTabBar({ activeTab, onChange }: ElectionInnerTabBarProps) {
  return (
    <div
      role="tablist"
      aria-label="선거 탭"
      className="flex overflow-x-auto border-b border-divider bg-white dark:border-dark-l dark:bg-dark-b scrollbar-hide">
      {TABS.map(({ key, label }) => {
        const isActive = key === activeTab;
        return (
          <button
            key={key}
            type="button"
            role="tab"
            aria-selected={isActive}
            onClick={() => onChange(key)}
            className={[
              'relative flex-1 min-w-[72px] h-10 px-0 text-sm font-medium transition-colors whitespace-nowrap',
              isActive ? 'text-primary-3 dark:text-gray-0.5' : 'text-gray-2 hover:text-gray-3 dark:hover:text-gray-1',
            ].join(' ')}>
            {label}
            {isActive && (
              <span
                aria-hidden="true"
                className="absolute bottom-0 left-0 h-[2px] w-full rounded-full bg-primary-3 dark:bg-gray-0.5"
              />
            )}
          </button>
        );
      })}
    </div>
  );
}
