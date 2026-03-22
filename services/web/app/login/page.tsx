'use client';

import { Logo } from '@/components';
import { Button, Link as NextUILink } from '@nextui-org/react';
import Image from 'next/image';

const buildOAuthHref = (provider: 'kakao' | 'google' | 'naver', callbackPath: string) => {
  const redirectUri = `${process.env.NEXT_PUBLIC_DOMAIN}${callbackPath}`;

  return `/v1/oauth2/authorization/${provider}?redirect_uri=${encodeURIComponent(redirectUri)}`;
};

export default function Login() {
  return (
    <section className="w-[90%] mx-auto flex flex-col items-center gap-8 mt-48 sm:w-[430px] ">
      <Logo width={222} height={37} />

      <Button
        as={NextUILink}
        href={buildOAuthHref('kakao', '/login/kakaoLogin')}
        variant="bordered"
        radius="full"
        startContent={<Image src="/images/kakao.svg" width={22} height={22} alt="카카오톡 로고 이미지" />}
        className="w-full h-[58px] bg-transparent border-gray-2 border-[1px]">
        카카오톡으로 시작하기
      </Button>
      <Button
        as={NextUILink}
        href={buildOAuthHref('google', '/login/googleLogin')}
        variant="bordered"
        radius="full"
        startContent={<Image src="/images/google.svg" width={22} height={22} alt="구글 로고 이미지" />}
        className="w-full h-[58px] bg-transparent border-gray-2 border-[1px]">
        구글로 시작하기
      </Button>
      <Button
        as={NextUILink}
        href={buildOAuthHref('naver', '/login/naverLogin')}
        variant="bordered"
        radius="full"
        startContent={<Image src="/images/naver.png" width={22} height={22} alt="네이버 로고 이미지" />}
        className="w-full h-[58px] bg-transparent border-gray-2 border-[1px]">
        네이버로 시작하기
      </Button>
    </section>
  );
}
