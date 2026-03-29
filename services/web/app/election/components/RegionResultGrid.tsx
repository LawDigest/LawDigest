'use client';

interface RegionResult {
  regionName: string;
  leadingParty: string;
  leadingPartyShort: string;
  percentage: number;
  partyColorClass: string;
}

interface RegionResultGridProps {
  regions: RegionResult[];
  onRegionClick?: (regionName: string) => void;
}

export default function RegionResultGrid({ regions, onRegionClick }: RegionResultGridProps) {
  return (
    <section className="px-5 flex flex-col gap-3">
      <p className="text-xs font-semibold tracking-widest text-gray-2 uppercase">지역별 현황</p>
      <div className="grid grid-cols-2 gap-2.5 sm:grid-cols-3">
        {regions.map((region) => (
          <button
            key={region.regionName}
            type="button"
            onClick={() => onRegionClick?.(region.regionName)}
            className="flex flex-col gap-2 rounded-xl bg-gray-0.5 dark:bg-dark-pb p-3.5 text-left transition hover:bg-gray-1 dark:hover:bg-dark-l active:scale-[0.97]">
            <div className="flex items-center justify-between gap-2">
              <span className="text-sm font-bold text-gray-4 dark:text-white leading-tight">{region.regionName}</span>
              <span
                className={`shrink-0 rounded-full px-2 py-0.5 text-[11px] font-bold text-white ${region.partyColorClass}`}>
                {region.leadingPartyShort}
              </span>
            </div>
            {/* 득표율 바 */}
            <div className="h-1.5 w-full rounded-full bg-gray-1 dark:bg-dark-l overflow-hidden">
              <div
                className={`h-full rounded-full transition-all ${region.partyColorClass}`}
                style={{ width: `${region.percentage}%` }}
              />
            </div>
            <p className="text-xs text-gray-2 tabular-nums">
              {region.percentage}% · {region.leadingParty}
            </p>
          </button>
        ))}
      </div>
    </section>
  );
}
