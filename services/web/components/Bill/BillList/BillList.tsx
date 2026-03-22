import { BillResponse, ValueOf } from '@/types';
import { RefObject } from 'react';
import { Spinner } from '@nextui-org/spinner';
import { FEED_TAB } from '@/constants';
import Bill from './Bill';

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
  return (
    <section className="xl:w-[840px]">
      {(bills || [])
        .filter((bill) => bill?.bill_info_dto)
        .map((bill, index) => (
          <Bill key={`${bill.bill_info_dto.bill_id + index}`} {...bill} detail={detail} />
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
