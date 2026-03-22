'use client';

import { useRouter } from 'next/navigation';
import { useState, useCallback, Dispatch, SetStateAction } from 'react';
import { IconSearchbar } from '@/public/svgs';
import { Button, Input } from '@nextui-org/react';
import { useResetRecoilState, useRecoilValue } from 'recoil';
import { searchModalState } from '@/store';

export default function SearchBar({
  setRecentKeywords,
}: {
  setRecentKeywords: Dispatch<SetStateAction<string[] | undefined>>;
}) {
  const router = useRouter();
  const [value, setValue] = useState('');
  const searchModal = useRecoilValue(searchModalState);
  const resetSearchModal = useResetRecoilState(searchModalState);

  const onSubmitSearch = useCallback(
    (event: React.FormEvent<HTMLFormElement> | React.MouseEvent<HTMLButtonElement>) => {
      event.preventDefault();
      const newKeyword = value.trim();

      if (newKeyword !== '') {
        const recentKeywords = JSON.parse(localStorage.getItem('recentKeywords') || '[]');

        if (recentKeywords.find((v: string) => v === newKeyword)) {
          const newRecentKeywords = [...recentKeywords.filter((v: string) => v !== newKeyword), newKeyword];
          localStorage.setItem('recentKeywords', JSON.stringify(newRecentKeywords));
          setRecentKeywords(newRecentKeywords);
        } else {
          const newRecentKeywords = [...recentKeywords, newKeyword];
          localStorage.setItem('recentKeywords', JSON.stringify(newRecentKeywords));
          setRecentKeywords(newRecentKeywords);
        }

        router.push(`/search/${value.trim()}`);
      } else {
        setValue('');
      }

      setValue('');
      resetSearchModal();
    },
    [value],
  );

  return (
    <form
      onSubmit={onSubmitSearch}
      className="w-full rounded-2xl flex justify-center items-center gap-[10px] md:w-[600px] mx-auto my-5">
      <Input
        autoFocus={searchModal.show}
        value={value}
        onValueChange={setValue}
        onClear={() => router.push('/search')}
        isClearable
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
          <Button size="sm" isIconOnly className="bg-transparent" onClick={onSubmitSearch}>
            <IconSearchbar />
          </Button>
        }
      />
    </form>
  );
}
