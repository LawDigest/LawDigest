'use client';

export type MapViewMode = 'geographic' | 'cartogram';

interface MapViewToggleProps {
  value: MapViewMode;
  onChange: (mode: MapViewMode) => void;
}

export default function MapViewToggle({ value, onChange }: MapViewToggleProps) {
  return (
    <div className="flex items-center self-end rounded-full bg-white dark:bg-dark-pb border border-gray-1 dark:border-dark-l shadow-sm p-1">
      {(['geographic', 'cartogram'] as const).map((mode) => {
        const isActive = value === mode;
        return (
          <button
            key={mode}
            type="button"
            aria-pressed={isActive}
            onClick={() => onChange(mode)}
            className={[
              'rounded-full px-3 py-1 text-xs font-semibold transition-all',
              isActive
                ? 'bg-gray-4 text-white dark:bg-white dark:text-gray-4 shadow-sm'
                : 'text-gray-2 hover:text-gray-3',
            ].join(' ')}>
            {mode === 'geographic' ? '실제 지도' : '카토그램'}
          </button>
        );
      })}
    </div>
  );
}
