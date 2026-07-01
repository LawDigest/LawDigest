'use client';

import { getPartyColor } from '@/constants/party';
import { useGetStatisticsByParty } from '../apis';

/** 정당별 대표발의 건수 막대. */
export default function StatsPartyBars() {
  const { data } = useGetStatisticsByParty();
  const parties = data?.data ?? [];

  if (parties.length === 0) return null;

  const max = Math.max(...parties.map((p) => p.count), 1);

  return (
    <div className="rounded-2xl border border-gray-1 bg-white p-4 shadow-sm dark:border-dark-l dark:bg-dark-b">
      <h2 className="mb-3 text-[14px] font-bold text-primary-3 dark:text-gray-0.5">정당별 발의 건수</h2>
      <div className="space-y-2.5 text-[12px]">
        {parties.map((party) => (
          <div key={party.party_id} className="flex items-center gap-2">
            <span className="w-[68px] shrink-0 truncate text-gray-3 dark:text-gray-1">{party.party_name}</span>
            <div className="h-5 flex-1 rounded-md bg-gray-0.5 dark:bg-dark-l">
              <div
                className="h-5 rounded-md"
                style={{ width: `${(party.count / max) * 100}%`, background: getPartyColor(party.party_name) }}
              />
            </div>
            <span className="w-10 shrink-0 text-right font-semibold text-primary-3 dark:text-gray-0.5">
              {party.count.toLocaleString()}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
