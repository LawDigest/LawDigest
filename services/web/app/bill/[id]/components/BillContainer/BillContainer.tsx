import { BillResponse } from '@/types';
import { BillDetail } from '..';

export default function BillContainer({ data, viewCount }: { data: BillResponse; viewCount: number }) {
  return (
    <section className="flex flex-col md:mb-10">
      <BillDetail data={data} viewCount={viewCount} />
    </section>
  );
}
