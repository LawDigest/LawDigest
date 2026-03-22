'use client';

import { useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@nextui-org/button';
import { IconArrowLeft } from '@/public/svgs';

export default function GoBackButton() {
  const router = useRouter();

  const onClick = useCallback(() => {
    router.back();
  }, []);

  return (
    <Button isIconOnly onClick={onClick} className="bg-transparent">
      <IconArrowLeft />
    </Button>
  );
}
