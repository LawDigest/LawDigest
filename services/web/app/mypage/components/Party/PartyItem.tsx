'use client';

import { useTheme } from 'next-themes';
import Image from 'next/image';
import Link from 'next/link';
import { FollowingPartyType } from '@/types';

export default function PartyItem({ party_id, party_name, party_image_url }: FollowingPartyType) {
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  return (
    <Link href={`/party/${party_id}`}>
      <div
        className={`w-[140px] h-[102px] rounded-lg mr-[10px] border-1.5 flex justify-center items-center ${party_name}`}>
        <Image
          src={`${process.env.NEXT_PUBLIC_IMAGE_URL}${isDark ? party_image_url.replace('wide', 'dark') : party_image_url}`}
          width={100}
          height={35}
          alt={`${party_name} 로고 이미지`}
          className="object-contain w-[100px] h-[35px] rounded-lg"
        />
      </div>
    </Link>
  );
}
