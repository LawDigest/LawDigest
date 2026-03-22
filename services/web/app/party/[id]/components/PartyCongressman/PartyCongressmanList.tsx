'use client';

import { useState, useCallback } from 'react';
import { useGetPartyCongressman } from '@/app/party/[id]/apis';
import { Spinner, Button, Divider } from '@nextui-org/react';
import { IconArrowDown, IconArrowUp } from '@/public/svgs';
import PartyCongressmanItem from './PartyCongressmanItem';

export default function PartyCongressmanList({ id }: { id: number }) {
  const { data, isFetching } = useGetPartyCongressman(id);
  const [isOpened, setIsOpened] = useState(false);

  const onClickButton = useCallback(() => {
    setIsOpened(!isOpened);
  }, [isOpened]);

  return (
    <section className="flex flex-col gap-5 mx-5 my-10">
      <div className="grid w-full grid-cols-4 md:grid-cols-8 lg:grid-cols-4 justify-items-center gap-y-3 ">
        {isOpened
          ? data?.data.party_congressman.map((congressman, index) => (
              <PartyCongressmanItem key={`${congressman.congressman_id + index}`} {...congressman} />
            ))
          : data?.data.party_congressman
              .slice(0, 8)
              .map((congressman, index) => (
                <PartyCongressmanItem key={`${congressman.congressman_id + index}`} {...congressman} />
              ))}
      </div>
      {isFetching && (
        <div className="flex justify-center w-full my-4">
          <Spinner color="default" />
        </div>
      )}
      <div
        className={`flex justify-center ${data?.data.party_congressman.length && data?.data.party_congressman.length <= 8 ? 'hidden' : ''}`}>
        <Button isIconOnly onClick={onClickButton} className="p-0 bg-transparent" size="sm">
          {isOpened ? <IconArrowUp /> : <IconArrowDown />}
        </Button>
      </div>

      <Divider className="dark:bg-dark-l lg:hidden" />
    </section>
  );
}
