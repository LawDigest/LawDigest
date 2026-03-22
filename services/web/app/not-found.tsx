'use client';

import { useRouter } from 'next/navigation';
import { Layout } from '@/components';
import Image from 'next/image';
import { Button } from '@nextui-org/react';

export default function NotFound() {
  const router = useRouter();

  return (
    <Layout nav logo notification>
      <section className="flex flex-col items-center justify-center h-full mt-20 md:mt-28">
        <Image
          src="/images/404-error.svg"
          width={500}
          height={240}
          alt="500 에러 이미지"
          className="mb-[40px] w-[269px] md:w-[500px] h-[180px] md:h-[240px]"
        />
        <h2 className="text-2xl md:text-[45px] font-extralight mb-[18px] md:mb-[28px]">페이지를 찾을 수 없습니다.</h2>
        <div className="flex flex-col md:flex-row gap-[10px]">
          <Button
            className="text-xl font-medium text-white rounded-none bg-primary-3 w-[261px] md:w-[227px] h-[56px] dark:bg-dark-pb lg:dark:bg-dark-b"
            onClick={() => router.back()}>
            이전 페이지
          </Button>
          <Button
            className="text-xl font-medium bg-white border rounded-none border-primary-3 w-[261px] md:w-[227px] h-[56px] dark:text-black"
            onClick={() => router.push('/')}>
            홈으로
          </Button>
        </div>
      </section>
    </Layout>
  );
}
