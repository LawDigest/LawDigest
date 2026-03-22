'use client';

import { useTheme } from 'next-themes';
import Link from 'next/link';
import { SearchCongressmanPartyProps } from '@/types';
import { EnterButton, PartyLogoReplacement } from '@/components';
import Image from 'next/image';

export default function SearchParty({ party_id, party_name, party_image_url }: SearchCongressmanPartyProps) {
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-6">
        {party_image_url !== null ? (
          <div
            className={`flex justify-center items-center w-[54px] h-[54px] border overflow-hidden rounded-full ${party_name}`}>
            <Image
              src={`${process.env.NEXT_PUBLIC_IMAGE_URL}${isDark ? party_image_url.replace('wide', 'dark') : party_image_url}`}
              width={40}
              height={16}
              alt={`${party_name} 로고 이미지`}
            />
          </div>
        ) : (
          <PartyLogoReplacement partyName={party_name} circle />
        )}
        <p className="text-lg font-semibold">{party_name}</p>
      </div>
      <Link href={`/party/${party_id}`}>
        <EnterButton />
      </Link>
    </div>
  );
}
