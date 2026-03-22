import { BillResponse } from '@/types';
import { RefObject } from 'react';
import { Spinner } from '@nextui-org/spinner';
import { Bill } from '@/components';

export default function BillFollowedList({
  bills,
  isFetching,
  fetchRef,
}: {
  bills: BillResponse[];
  isFetching: boolean;
  fetchRef: RefObject<HTMLDivElement>;
}) {
  return (
    <ul className="flex flex-col gap-4">
      {bills.map((bill) => (
        <Bill {...bill} key={bill.bill_info_dto.bill_id} />
      ))}
      {isFetching && (
        <div className="flex justify-center w-full my-4">
          <Spinner color="default" />
        </div>
      )}
      <div ref={fetchRef} />
    </ul>
  );
}
