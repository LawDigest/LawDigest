'use client';

import { BillDetail } from '..';

export default function BillContainer({ id, viewCount }: { id: string; viewCount: number }) {
  return (
    <section className="flex flex-col md:mb-10">
      <BillDetail id={id} viewCount={viewCount} />
    </section>
  );
}
