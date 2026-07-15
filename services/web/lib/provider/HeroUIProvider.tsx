'use client';

import { HeroUIProvider as Provider } from '@heroui/react';
import { useRouter } from 'next/navigation';

export default function HeroUIProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();

  return <Provider navigate={router.push}>{children}</Provider>;
}
