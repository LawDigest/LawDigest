'use client';

import CongressmanDetail from '../Congressman/CongressmanDetail';
import BillContainer from '../BillContainer';

export default function CongressmanContainer({ id }: { id: string }) {
  return (
    <div className="xl:flex xl:items-start xl:justify-center xl:gap-10">
      <CongressmanDetail congressmanId={id} />
      <BillContainer id={id} />
    </div>
  );
}
