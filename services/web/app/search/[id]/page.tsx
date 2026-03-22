'use client';

import { useState, useEffect } from 'react';
import { BillList, SearchBarButton } from '@/components';
import { useIntersect } from '@/hooks';
import { Divider } from '@nextui-org/react';
import { useGetSearchCongressmanParty, useGetSearchBill } from '../apis';
import { SearchList } from './components';

export default function SearchResult({ params: { id } }: { params: { id: string } }) {
  const { data: dataCP, refetch: refetchCP } = useGetSearchCongressmanParty(decodeURI(id));
  const {
    data: dataBill,
    hasNextPage: hasNextPageBill,
    isFetching: isFetchingBill,
    fetchNextPage: fetchNextPageBill,
    refetch: refetchBill,
  } = useGetSearchBill(decodeURI(id));
  const [searchResultsCP, setSearchResultsCP] = useState(dataCP ? dataCP.data.search_response : []);
  const [searchResultsBill, setSearchResultsBill] = useState(
    dataBill ? dataBill.pages.flatMap(({ data: { search_response: responses } }) => responses) : [],
  );

  const fetchRefBill = useIntersect(async (entry: any, observer: any) => {
    observer.unobserve(entry.target);
    if (hasNextPageBill && !isFetchingBill) {
      fetchNextPageBill();
    }
  });

  useEffect(() => {
    if (dataCP) {
      setSearchResultsCP(() => [...dataCP.data.search_response]);
    }
    if (dataBill) {
      setSearchResultsBill(() => [...dataBill.pages.flatMap(({ data: { search_response: responses } }) => responses)]);
    }
  }, [dataCP, dataBill]);

  useEffect(() => {
    refetchCP();
    refetchBill();
  }, [dataCP, dataBill]);

  return (
    <>
      <SearchBarButton />
      <section className="lg:w-[840px] mx-auto">
        <p className="mx-5 my-4 text-sm font-medium text-center md:text-base text-gray-2">{`'${decodeURI(id)}'에 대한 검색 결과입니다.`}</p>
        <div className="mb-10">
          <div>
            <h2 className="mx-5 text-lg font-semibold md:text-xl">의원 · 정당</h2>
            <div className="flex justify-center mx-5">
              <Divider className="my-2 bg-gray-1 dark:bg-dark-l" />
            </div>
            {searchResultsCP.length ? (
              <SearchList searchResults={searchResultsCP} />
            ) : (
              <p className="my-8 text-sm text-center md:text-base text-gray-2">검색 결과가 존재하지 않습니다.</p>
            )}
          </div>

          <div>
            <h2 className="mx-5 text-lg font-semibold md:text-xl">법안</h2>
            <div className="flex justify-center mx-5">
              <Divider className="mx-5 mt-2 bg-gray-1 dark:bg-dark-l" />
            </div>
            {searchResultsBill.length ? (
              <BillList bills={searchResultsBill} isFetching={isFetchingBill} fetchRef={fetchRefBill} detail={false} />
            ) : (
              <p className="my-8 text-sm text-center md:text-base text-gray-2">검색 결과가 존재하지 않습니다.</p>
            )}
          </div>
        </div>
      </section>
    </>
  );
}
