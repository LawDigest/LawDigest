'use client';

import { useCallback, useState, useEffect } from 'react';
import { IconArrowUp } from '@/public/svgs';
import { Button } from '@nextui-org/react';

export default function GoToTopButton() {
  const [isVisible, setIsVisible] = useState(false);

  const handleScroll = useCallback(() => {
    const { scrollY } = window;

    if (scrollY > 400) {
      setIsVisible(true);
    } else {
      setIsVisible(false);
    }
  }, []);

  const onClickGoToTopButton = useCallback(() => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, []);

  useEffect(() => {
    window.addEventListener('scroll', handleScroll);

    return () => {
      window.removeEventListener('scroll', handleScroll);
    };
  }, []);

  return (
    <Button
      isIconOnly
      className={`${isVisible ? '' : 'hidden'} z-10 fixed bg-gray-1/80 dark:bg-gray-3/60 bottom-24 right-10 md:bottom-20 md:right-20`}
      variant="light"
      onClick={onClickGoToTopButton}>
      <IconArrowUp />
    </Button>
  );
}
