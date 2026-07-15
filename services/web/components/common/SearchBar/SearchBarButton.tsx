'use client';

import { useCallback } from 'react';
import { useSetAtom } from 'jotai';
import { Input, Button } from '@heroui/react';
import { searchModalState } from '@/store';
import { IconSearchbar } from '@/public/svgs';

export default function SearchBarButton() {
  const setSearchModal = useSetAtom(searchModalState);

  const onClickSearchBar = useCallback(() => {
    setSearchModal({ show: true });
  }, []);

  return (
    // eslint-disable-next-line jsx-a11y/click-events-have-key-events
    <form
      onClick={onClickSearchBar}
      className="w-full px-5 rounded-2xl flex justify-center items-center gap-[10px] md:w-[600px] mx-auto my-5">
      <Input
        isReadOnly
        radius="lg"
        classNames={{
          input: ['bg-transparent', 'text-black/90', 'truncate'],
          inputWrapper: [
            'h-[40px]',
            'w-full',
            'shadow-sm',
            'group-data-[focused=true]:bg-default-200/50',
            '!cursor-text',
          ],
        }}
        placeholder="법안, 의원, 정당명으로 검색"
        endContent={
          <Button size="sm" isIconOnly className="bg-transparent">
            <IconSearchbar />
          </Button>
        }
      />
    </form>
  );
}
