'use client';

import { useTheme } from 'next-themes';
import Image from 'next/image';

export default function PartyLogo({ party_name, party_img_url }: { party_name: string; party_img_url: string }) {
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  return (
    <div className={`shadow-lg rounded-full w-[130px] h-[130px] flex justify-center items-center border ${party_name}`}>
      <Image
        src={`${process.env.NEXT_PUBLIC_IMAGE_URL}${isDark ? party_img_url.replace('wide', 'dark') : party_img_url}`}
        width={200}
        height={90}
        alt={`${party_name} 로고 이미지`}
        className="w-[100px] h-[45px] object-contain"
      />
    </div>
  );
}
