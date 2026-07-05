'use client';

import { CSSProperties, useEffect, useState } from 'react';
import Link from 'next/link';
import { Avatar } from '@nextui-org/avatar';
import { Spinner } from '@nextui-org/spinner';
import { getPartyColor } from '@/constants/party';
import { useIntersect } from '@/hooks';
import { CongressmanRanking, useGetCongressmanList } from '../apis';

/** 의원 전체 리스트 — 대표발의 건수 순, 무한 스크롤. */
export default function MemberList() {
  const { data, hasNextPage, isFetching, fetchNextPage } = useGetCongressmanList();
  const [members, setMembers] = useState<CongressmanRanking[]>(
    data ? data.pages.flatMap(({ data: { congressman_list } }) => congressman_list) : [],
  );

  const fetchRef = useIntersect(async (entry: IntersectionObserverEntry, observer: IntersectionObserver) => {
    observer.unobserve(entry.target);
    if (hasNextPage && !isFetching) {
      fetchNextPage();
    }
  });

  useEffect(() => {
    if (data) {
      setMembers([...data.pages.flatMap(({ data: { congressman_list } }) => congressman_list)]);
    }
  }, [data]);

  if (members.length === 0 && !isFetching) {
    return <div className="py-10 text-center text-[14px] text-gray-2">의원 정보가 없습니다.</div>;
  }

  return (
    <div className="flex flex-col gap-2.5">
      <div className="grid grid-cols-1 gap-2.5 md:grid-cols-2">
        {members.map((member) => (
          <Link
            key={member.congressman_id}
            href={`/congressman/${member.congressman_id}`}
            className="flex items-center gap-3 rounded-2xl border border-gray-1 bg-white p-3.5 shadow-sm transition-colors hover:bg-primary-1 dark:border-dark-l dark:bg-dark-b dark:hover:bg-dark-l">
            <Avatar
              src={process.env.NEXT_PUBLIC_IMAGE_URL + member.congressman_image_url}
              alt={member.congressman_name}
              className="h-12 w-12 shrink-0 bg-white ring-2"
              style={{ '--tw-ring-color': getPartyColor(member.party_name) } as CSSProperties}
            />
            <div className="min-w-0 flex-1">
              <p className="text-[15px] font-bold text-primary-3 dark:text-gray-0.5">{member.congressman_name}</p>
              <div className="mt-0.5 flex items-center gap-1.5 text-[12px]">
                <span
                  className="rounded px-1.5 py-0.5 text-[11px] font-medium text-white"
                  style={{ background: getPartyColor(member.party_name) }}>
                  {member.party_name}
                </span>
                <span className="text-gray-2">대표발의 {member.propose_count.toLocaleString()}건</span>
              </div>
            </div>
          </Link>
        ))}
      </div>
      {isFetching && (
        <div className="flex justify-center py-4">
          <Spinner color="default" />
        </div>
      )}
      <div ref={fetchRef} />
    </div>
  );
}
