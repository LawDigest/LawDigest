import { BillProps } from '@/types';
import { AnotherBill } from '.';

export default function AnotherBillList({ bill_info_dto, similar_bills }: BillProps) {
  return (
    <section className="flex flex-col gap-4 lg:gap-6">
      <div>
        <h3 className="mb-2 text-2xl font-semibold lg:mb-0">
          <span className="text-gray-3 dark:text-gray-2">{bill_info_dto.bill_name}</span>의 다른 개정안 보기
        </h3>
      </div>
      {similar_bills.length === 0 && (
        <p className="text-sm text-gray-2 dark:text-gray-3 lg:text-base">
          해당 법안과 관련된 다른 개정안이 존재하지 않습니다.
        </p>
      )}
      {similar_bills.map((similarBill) => (
        <AnotherBill key={similarBill.billId} {...similarBill} />
      ))}
    </section>
  );
}
