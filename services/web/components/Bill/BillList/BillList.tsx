import { BillResponse, ValueOf } from '@/types';
import { RefObject } from 'react';
import { Spinner } from '@nextui-org/spinner';
import { FEED_TAB } from '@/constants';
import Bill from './Bill';
import { filterUniqueBills } from './filterUniqueBills';

export default function BillList({
  bills,
  isFetching,
  fetchRef,
  detail,
  feedType,
}: {
  bills: BillResponse[];
  isFetching: boolean;
  fetchRef: RefObject<HTMLDivElement>;
  detail?: boolean;
  feedType?: ValueOf<typeof FEED_TAB>;
}) {
  const uniqueBills = filterUniqueBills(bills);

  return (
    <section className="xl:w-[840px]">
      {uniqueBills.map((bill) => (
        <Bill key={bill.bill_info_dto.bill_id} {...bill} detail={detail} />
      ))}
      {feedType === 'sorted_by_latest' && isFetching && (
        <div className="flex justify-center w-full my-4">
          <Spinner color="default" />
        </div>
      )}
      <div ref={fetchRef} />
    </section>
  );
}
