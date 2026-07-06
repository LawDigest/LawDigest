'use client';

export type AssemblySegmentValue = 'member' | 'party';

const SEGMENTS: { key: AssemblySegmentValue; label: string }[] = [
  { key: 'member', label: '의원' },
  { key: 'party', label: '정당' },
];

interface AssemblySegmentProps {
  active: AssemblySegmentValue;
  onChange: (value: AssemblySegmentValue) => void;
}

/** 국회 패널 상단 의원/정당 세그먼트 컨트롤. */
export default function AssemblySegment({ active, onChange }: AssemblySegmentProps) {
  return (
    <div
      role="tablist"
      aria-label="국회 하위 세그먼트"
      className="inline-flex self-start rounded-full bg-gray-0.5 p-1 text-[13px] font-semibold dark:bg-dark-l">
      {SEGMENTS.map(({ key, label }) => {
        const isActive = key === active;
        return (
          <button
            key={key}
            type="button"
            role="tab"
            aria-selected={isActive}
            onClick={() => onChange(key)}
            className={[
              'rounded-full px-5 py-1.5 transition-colors',
              isActive
                ? 'bg-primary-3 text-white dark:bg-gray-0.5 dark:text-black'
                : 'text-gray-2 hover:text-gray-3 dark:hover:text-gray-1',
            ].join(' ')}>
            {label}
          </button>
        );
      })}
    </div>
  );
}
