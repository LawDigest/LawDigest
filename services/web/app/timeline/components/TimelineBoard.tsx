'use client';

import { useEffect, useState } from 'react';
import { Divider, Card, CardBody } from '@nextui-org/react';
import { getDDay } from '@/utils';
import { TimelineBillState } from '@/types';
import { useGetTimelineBillState } from '../apis/queries';

export default function TimelineBoard() {
  const { data } = useGetTimelineBillState();
  const [billState, setBillState] = useState<TimelineBillState>();

  useEffect(() => {
    if (data) {
      setBillState(data.data);
    }
  }, [data]);

  return (
    <Card
      classNames={{
        base: ['shadow-[0_4px_6px_-2px_rgba(0,_0,_0,_0.1)] md:shadow-none'],
      }}
      className="w-full border-b md:border-none dark:border-dark-l mx-auto bg-transparent md:dark:bg-primary-3 md:mt-10 md:mb-6 md:w-[708px] md:pt-3 md:rounded-xl">
      <CardBody className="flex flex-col items-center gap-1 md:flex-row md:justify-center md:gap-[50px] md:shadow-none">
        <div className="flex flex-col items-center gap-3 md:flex-row md:gap-6">
          <h2 className="font-semibold text-[26px] md:text-[48px] md:font-bold">타임라인</h2>
          <div className="flex items-center justify-center gap-3 md:flex-col md:gap-1">
            <p className="text-xs font-semibold text-gray-2 md:text-[20px] md:font-normal">제 22대 국회</p>
            <Divider orientation="vertical" className="h-4 w-[1px] bg-black md:hidden" />
            <p className="text-lg font-semibold">{`D-${getDDay('2028-04-11')}`}</p>
          </div>
        </div>
        <Divider orientation="vertical" className="h-[82px] bg-gray-2 hidden md:block" />
        <div className="flex gap-10">
          <div className="flex flex-col items-center gap-2">
            <span className="text-2xl font-semibold">{billState && billState.receipt_count}</span>
            <span className="text-sm font-medium text-gray-2">접수법안</span>
          </div>
          <div className="flex flex-col items-center gap-2">
            <span className="text-2xl font-semibold">{billState && billState.treatment_count}</span>
            <span className="text-sm font-medium text-gray-2">처리법안</span>
          </div>
          <div className="flex flex-col items-center gap-2">
            <span className="text-2xl font-semibold">{billState && billState.passed_count}</span>
            <span className="text-sm font-medium text-gray-2">가결법안</span>
          </div>
        </div>
      </CardBody>
    </Card>
  );
}
