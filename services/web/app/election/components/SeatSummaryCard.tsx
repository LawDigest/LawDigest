'use client';

interface SeatParty {
  name: string;
  seats: number;
  colorClass: string;
}

interface SeatSummaryCardProps {
  totalSeats: number;
  countRate: number;
  parties: SeatParty[];
}

export default function SeatSummaryCard({ totalSeats, countRate, parties }: SeatSummaryCardProps) {
  const seatsAllocated = parties.reduce((sum, p) => sum + p.seats, 0);

  return (
    <section className="mx-5 rounded-2xl bg-white dark:bg-dark-pb border border-gray-1 dark:border-dark-l shadow-sm p-4 flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <p className="text-xs font-semibold tracking-widest text-gray-2 uppercase">의석 현황</p>
        <span className="text-xs text-gray-2">
          개표율 <span className="font-bold text-gray-4 dark:text-white">{countRate}%</span>
        </span>
      </div>

      {/* 의석 바 */}
      <div className="flex h-3 w-full overflow-hidden rounded-full" role="img" aria-label="정당별 의석 비율">
        {parties.map((party) => (
          <div
            key={party.name}
            className={`h-full transition-all ${party.colorClass}`}
            style={{ width: `${(party.seats / seatsAllocated) * 100}%` }}
          />
        ))}
      </div>

      {/* 정당별 의석 수 */}
      <div className="flex flex-wrap gap-x-4 gap-y-2">
        {parties.map((party) => (
          <div key={party.name} className="flex items-center gap-1.5">
            <span className={`h-2.5 w-2.5 rounded-full ${party.colorClass}`} />
            <span className="text-xs text-gray-3 dark:text-gray-1">{party.name}</span>
            <span className="text-sm font-bold text-gray-4 dark:text-white tabular-nums">
              {party.seats}
              <span className="text-xs font-normal text-gray-2">석</span>
            </span>
          </div>
        ))}
        <div className="flex items-center gap-1.5 ml-auto">
          <span className="text-xs text-gray-2">총</span>
          <span className="text-sm font-bold text-gray-4 dark:text-white tabular-nums">
            {totalSeats}
            <span className="text-xs font-normal text-gray-2">석</span>
          </span>
        </div>
      </div>
    </section>
  );
}
