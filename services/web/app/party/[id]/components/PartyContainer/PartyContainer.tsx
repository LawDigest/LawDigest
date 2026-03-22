'use client';

import { PartyDetail } from '../PartyDetail';
import { PartyCongressmanList } from '../PartyCongressman';
import { BillContainer } from '../BillContainer';

export default function PartyContainer({ id }: { id: string }) {
  return (
    <div className="xl:flex xl:justify-center xl:gap-10">
      <div>
        <PartyDetail partyId={Number(id)} />
        <PartyCongressmanList id={Number(id)} />
      </div>
      <div className="">
        <BillContainer id={Number(id)} />
      </div>
    </div>
  );
}
