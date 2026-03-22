'use client';

import { useRouter } from 'next/navigation';
import { useCallback, useState, useEffect } from 'react';
import { useRecoilValue, useResetRecoilState } from 'recoil';
import { searchModalState } from '@/store';
import { Button, Chip } from '@nextui-org/react';
import { IconX } from '@/public/svgs';
import SearchBar from './SearchBar';

export default function SearchModal() {
  const router = useRouter();
  const searchModal = useRecoilValue(searchModalState);
  const resetSearchModal = useResetRecoilState(searchModalState);
  const [recentKeywords, setRecentKeywords] = useState(
    typeof window !== 'undefined' ? JSON.parse(localStorage.getItem('recentkeywords') || '[]') : [],
  );

  const closeModal = useCallback(() => {
    resetSearchModal();
  }, []);

  const onClickRemoveAll = useCallback(() => {
    setRecentKeywords([]);
    localStorage.setItem('recentKeywords', JSON.stringify([]));
  }, [recentKeywords]);

  const onClickChip = useCallback((searchWord: string) => {
    router.push(`/search/${searchWord}`);
    resetSearchModal();
  }, []);

  const onClickRemoveRecentKeyword = useCallback(
    (keyword: string) => {
      const newRecentKeywords = recentKeywords.filter((v: string) => v !== keyword);
      setRecentKeywords(newRecentKeywords);
      localStorage.setItem('recentKeywords', JSON.stringify(newRecentKeywords));
    },
    [recentKeywords],
  );

  useEffect(() => {
    if (typeof window !== 'undefined') {
      setRecentKeywords(JSON.parse(localStorage.getItem('recentKeywords') || '[]'));
    }
  }, [searchModal]);

  useEffect(() => {
    if (recentKeywords.length > 10) {
      const newRecentKeywords = recentKeywords.slice(1);
      setRecentKeywords(newRecentKeywords);
      localStorage.setItem('recentKeywords', JSON.stringify(newRecentKeywords));
    }
  }, [recentKeywords]);

  return (
    <section
      className={`inset-0 w-full dark:bg-dark-b/80 bg-white/80 backdrop-blur-[10px] z-10 flex justify-center ${searchModal.show ? 'fixed' : 'hidden'}`}>
      <div className="mx-5 mt-10 md:mt-20 w-full md:w-[600px]">
        <div className="flex flex-col gap-4 md:relative">
          <div className="-right-20 md:absolute top-[22px]">
            <Button onClick={closeModal} className="float-right p-0 bg-transparent" size="sm" isIconOnly>
              <IconX />
            </Button>
          </div>
          <SearchBar setRecentKeywords={setRecentKeywords} />

          <section className="flex flex-col gap-7">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold md:text-xl">최근 검색어</h2>
              <Button
                size="sm"
                className="p-0 text-xs font-medium bg-transparent text-gray-2 md:text-sm"
                onClick={onClickRemoveAll}>
                모두 지우기
              </Button>
            </div>
            <div className="flex gap-[10px] flex-wrap">
              {recentKeywords && recentKeywords.length > 0 ? (
                recentKeywords.map((keyword: string) => (
                  <Chip
                    key={keyword}
                    variant="bordered"
                    className="h-7 md:h-8 border-gray-2 border-1 text-gray-3 dark:text-gray-2 dark:border-gray-3"
                    onClick={() => onClickChip(keyword)}
                    onClose={() => {
                      onClickRemoveRecentKeyword(keyword);
                    }}>
                    <p className="cursor-pointer max-w-[280px] truncate">{keyword}</p>
                  </Chip>
                ))
              ) : (
                <p className="text-sm text-gray-3 dark:text-gray-2">최근 검색어가 존재하지 않습니다.</p>
              )}
            </div>
          </section>
        </div>
      </div>
    </section>
  );
}
