'use client';

import { getPartyColor } from '@/constants/party';
import { useGetParliamentaryParties } from '../apis';

/** 제22대 국회 의석 분포 strip — /party/parliamentary(정당별 소속 의원 수) 기반. */
export default function SeatDistribution() {
  const { data } = useGetParliamentaryParties();
  const parties = [...(data?.data ?? [])].sort((a, b) => b.congressman_count - a.congressman_count);
  const total = parties.reduce((sum, p) => sum + p.congressman_count, 0);

  if (total === 0) return null;

  return (
    <section className="rounded-2xl border border-gray-1 bg-white p-4 shadow-sm dark:border-dark-l dark:bg-dark-b">
      <div className="mb-2.5 flex items-baseline justify-between">
        <h2 className="text-[14px] font-bold text-primary-3 dark:text-gray-0.5">제22대 국회 의석 분포</h2>
        <span className="text-[12px] text-gray-2">재적 {total.toLocaleString()}석</span>
      </div>

      <div className="flex h-3 w-full overflow-hidden rounded-full">
        {parties.map((party) => (
          <div
            key={party.party_id}
            style={{
              width: `${(party.congressman_count / total) * 100}%`,
              background: getPartyColor(party.party_name),
            }}
            title={`${party.party_name} ${party.congressman_count}석`}
          />
        ))}
      </div>

      <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1.5 text-[12px] text-gray-3 dark:text-gray-1">
        {parties.map((party) => (
          <span key={party.party_id} className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full" style={{ background: getPartyColor(party.party_name) }} />
            {party.party_name} {party.congressman_count.toLocaleString()}
          </span>
        ))}
      </div>
    </section>
  );
}
