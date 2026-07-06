'use client';

import { useTheme } from 'next-themes';
import Link from 'next/link';
import Image from 'next/image';
import { getPartyColor } from '@/constants/party';
import { getPartyLogoSrc } from '@/utils';
import { useGetParliamentaryParties } from '../apis';

/** 정당 탭 — 원내 정당 목록(소속 의원 수 순). 각 항목은 정당 상세로 이동. */
export default function PartyList() {
  const { theme } = useTheme();
  const isDark = theme === 'dark';
  const { data, isLoading } = useGetParliamentaryParties();
  const parties = [...(data?.data ?? [])].sort((a, b) => b.congressman_count - a.congressman_count);

  if (isLoading) {
    return <div className="py-10 text-center text-[14px] text-gray-2">정당을 불러오는 중…</div>;
  }

  return (
    <div className="grid grid-cols-1 gap-2.5 md:grid-cols-2">
      {parties.map((party) => (
        <Link
          key={party.party_id}
          href={`/party/${party.party_id}`}
          style={{ borderColor: getPartyColor(party.party_name) }}
          className="flex items-center gap-3 rounded-2xl border bg-white p-3.5 shadow-sm transition-colors hover:bg-primary-1 dark:bg-dark-b dark:hover:bg-dark-l">
          {(() => {
            const logoSrc = getPartyLogoSrc(party.party_image_url, isDark);
            return logoSrc ? (
              // 원형 크롭 없이 전체 로고가 보이도록 object-contain.
              <span className="flex h-11 w-11 shrink-0 items-center justify-center">
                <Image
                  src={logoSrc}
                  alt={`${party.party_name} 로고`}
                  width={44}
                  height={44}
                  className="h-11 w-11 object-contain"
                />
              </span>
            ) : (
              <span
                className="grid h-11 w-11 shrink-0 place-items-center rounded-full text-[14px] font-bold text-white"
                style={{ background: getPartyColor(party.party_name) }}>
                {party.party_name.trim().charAt(0)}
              </span>
            );
          })()}
          <div className="min-w-0 flex-1">
            <p className="text-[15px] font-bold text-primary-3 dark:text-gray-0.5">{party.party_name}</p>
            <p className="mt-0.5 text-[12px] text-gray-2">소속 의원 {party.congressman_count.toLocaleString()}명</p>
          </div>
          <span className="material-symbols-outlined text-[20px] text-gray-2">chevron_right</span>
        </Link>
      ))}
    </div>
  );
}
