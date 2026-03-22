'use client';

import { useEffect, useState } from 'react';
import { FollowingCongressmanType, FollowingCongressmanResponse } from '@/types';
import { ExpandableList } from '@/components';
import CongressmanItem from './CongressmanItem';
import { useGetFollowingCongressman } from '../../apis';

export default function CongressmanList() {
  const { data } = useGetFollowingCongressman();
  const [congressmanList, setConressmanList] = useState<FollowingCongressmanResponse>();

  useEffect(() => {
    if (data) {
      setConressmanList(data.data);
    }
  }, [data]);

  return (
    <section className="px-[30px] flex flex-col gap-6">
      <p className="text-xl font-semibold">
        팔로우한 의원 &middot;<span className="text-[#555555] dark:text-gray-2"> {congressmanList?.length}</span>
      </p>

      {congressmanList && (
        <ExpandableList
          items={congressmanList.map((congressman: FollowingCongressmanType) => (
            <CongressmanItem key={congressman.congressman_id} {...congressman} />
          ))}
          initialCount={8}
        />
      )}
    </section>
  );
}
