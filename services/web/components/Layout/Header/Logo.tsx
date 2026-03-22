'use client';

import Image from 'next/image';
import { useTheme } from 'next-themes';

interface LogoProps {
  width: number;
  height: number;
}

export default function Logo({ width, height }: LogoProps) {
  const { theme } = useTheme();

  return (
    <Image
      priority
      src={theme === 'dark' ? '/images/logoDark.svg' : '/images/logo.svg'}
      width={width}
      height={height}
      alt="로고이미지"
    />
  );
}
