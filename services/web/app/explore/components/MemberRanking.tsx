'use client';

import { CSSProperties } from 'react';
import Link from 'next/link';
import { Avatar } from '@nextui-org/avatar';
import { getPartyColor } from '@/constants/party';
import { useGetCongressmanRanking } from '../apis';

const RANK_BADGE = ['bg-primary-3 text-white', 'bg-gray-3 text-white', 'bg-gray-2 text-white'];

/** 발의 활발한 의원 랭킹(상위 3명) — 대표발의 건수 순. */
export default function MemberRanking() {
  const { data } = useGetCongressmanRanking(3);
  const ranking = data?.data ?? [];

  if (ranking.length === 0) return null;

  return (
    <section className="flex flex-col gap-3">
      <div className="flex items-center gap-1.5">
        <span className="material-symbols-outlined text-[20px] text-theme-alert">trending_up</span>
        <h2 className="text-[15px] font-bold text-primary-3 dark:text-gray-0.5">발의 활발한 의원</h2>
      </div>
      <div className="-mx-4 flex gap-3 overflow-x-auto px-4 scrollbar-hide md:mx-0 md:grid md:grid-cols-3 md:overflow-visible md:px-0">
        {ranking.map((member, index) => (
          <Link
            key={member.congressman_id}
            href={`/congressman/${member.congressman_id}`}
            className="relative w-[128px] shrink-0 rounded-2xl border border-gray-1 bg-white p-3 text-center shadow-sm transition-colors hover:bg-primary-1 dark:border-dark-l dark:bg-dark-b dark:hover:bg-dark-l md:w-auto">
            <span
              className={`absolute left-2.5 top-2.5 grid h-5 w-5 place-items-center rounded-full text-[11px] font-bold ${
                RANK_BADGE[index] ?? 'bg-gray-2 text-white'
              }`}>
              {index + 1}
            </span>
            <Avatar
              src={member.congressman_image_url}
              alt={member.congressman_name}
              className="mx-auto h-14 w-14 bg-white ring-2"
              style={{ '--tw-ring-color': getPartyColor(member.party_name) } as CSSProperties}
            />
            <p className="mt-2 text-[14px] font-bold text-primary-3 dark:text-gray-0.5">{member.congressman_name}</p>
            <p className="text-[11px]" style={{ color: getPartyColor(member.party_name) }}>
              {member.party_name}
            </p>
            <p className="mt-1 text-[12px] text-gray-3 dark:text-gray-1">
              대표발의 <b className="text-primary-3 dark:text-gray-0.5">{member.propose_count}</b>건
            </p>
          </Link>
        ))}
      </div>
    </section>
  );
}
