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
    <nav
      aria-label="선거 탭"
      className="flex border-b border-gray-1 dark:border-dark-l bg-white dark:bg-dark-b overflow-x-auto scrollbar-hide">
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
              'relative flex-1 min-w-[72px] py-3 text-sm font-semibold transition-colors whitespace-nowrap',
              isActive ? 'text-gray-4 dark:text-white' : 'text-gray-2 hover:text-gray-3 dark:hover:text-gray-1',
            ].join(' ')}>
            {label}
            {isActive && (
              <span
                aria-hidden="true"
                className="absolute bottom-0 left-1/2 -translate-x-1/2 h-[3px] w-8 rounded-full bg-gradient-to-r from-primary-2 to-primary-3"
              />
            )}
          </button>
        );
      })}
    </nav>
  );
}
