'use client';

interface GovernorParty {
  name: string;
  seats: number;
  color: string;
}

interface PollSegment {
  label: string;
  count: number;
  color: string;
}

interface SeatSummaryCardProps {
  totalRegions: number;
  governorParties: GovernorParty[];
  pollSegments: PollSegment[];
}

export default function SeatSummaryCard({ totalRegions, governorParties, pollSegments }: SeatSummaryCardProps) {
  const governorTotal = governorParties.reduce((sum, p) => sum + p.seats, 0);
  const pollTotal = pollSegments.reduce((sum, s) => sum + s.count, 0);

  return (
    <section className="mx-5 rounded-xl bg-white dark:bg-dark-pb border border-gray-1 dark:border-dark-l shadow-none p-4 flex flex-col gap-4">
      {/* 현직 광역단체장 현황 */}
      <div className="flex flex-col gap-2">
        <p className="text-xs font-semibold tracking-widest text-gray-2 uppercase">현직 광역단체장 현황</p>
        <div className="flex h-3 w-full overflow-hidden rounded-full" role="img" aria-label="정당별 광역단체장 수">
          {governorParties.map((p) => (
            <div
              key={p.name}
              className="h-full transition-all"
              style={{ backgroundColor: p.color, width: `${(p.seats / governorTotal) * 100}%` }}
            />
          ))}
        </div>
        <div className="flex flex-wrap gap-x-4 gap-y-1">
          {governorParties.map((p) => (
            <div key={p.name} className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full" style={{ backgroundColor: p.color }} />
              <span className="text-xs text-gray-3 dark:text-gray-1">{p.name}</span>
              <span className="text-sm font-bold text-gray-4 dark:text-white tabular-nums">
                {p.seats}
                <span className="text-xs font-normal text-gray-2">곳</span>
              </span>
            </div>
          ))}
          <div className="flex items-center gap-1 ml-auto">
            <span className="text-xs text-gray-2">총</span>
            <span className="text-sm font-bold text-gray-4 dark:text-white tabular-nums">
              {totalRegions}
              <span className="text-xs font-normal text-gray-2">곳</span>
            </span>
          </div>
        </div>
      </div>

      <div className="border-t border-gray-1 dark:border-dark-l" />

      {/* 여론조사 현황 */}
      <div className="flex flex-col gap-2">
        <p className="text-xs font-semibold tracking-widest text-gray-2 uppercase">여론조사 현황</p>
        <div className="flex h-3 w-full overflow-hidden rounded-full" role="img" aria-label="여론조사 우세 현황">
          {pollSegments.map((s) => (
            <div
              key={s.label}
              className="h-full transition-all"
              style={{ backgroundColor: s.color, width: `${(s.count / pollTotal) * 100}%` }}
            />
          ))}
        </div>
        <div className="flex flex-wrap gap-x-4 gap-y-1">
          {pollSegments.map((s) => (
            <div key={s.label} className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full" style={{ backgroundColor: s.color }} />
              <span className="text-xs text-gray-3 dark:text-gray-1">{s.label}</span>
              <span className="text-sm font-bold text-gray-4 dark:text-white tabular-nums">
                {s.count}
                <span className="text-xs font-normal text-gray-2">곳</span>
              </span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
