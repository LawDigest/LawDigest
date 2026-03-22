'use client';

import { useEffect } from 'react';
import { Logo } from '@/components';
import { useRouter } from 'next/navigation';

export default function KaKaoLogin() {
  const router = useRouter();

  useEffect(() => {
    router.push('/mypage');
  }, [router]);

  return (
    <section className="w-[90%] mx-auto h-full flex flex-col justify-center items-center gap-20">
      <Logo width={222} height={37} />

      <p>로그인 중입니다.</p>
    </section>
  );
}
