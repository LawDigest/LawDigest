'use client';

import Link from 'next/link';
import Image from 'next/image';
import { useTheme } from 'next-themes';
import { Card, CardBody, Chip, Button, useDisclosure, Pagination } from '@nextui-org/react';
import { ProcessResult } from '@/app/bill/[id]/components';
import { useState, useEffect } from 'react';
import { IconEnter, IconNext, IconPrev } from '@/public/svgs';
import TimelineModal from './TimelineModal';

export default function PlenaryList({
  plenary_list,
}: {
  plenary_list: {
    bill_info: {
      party_info: {
        party_id: number;
        party_name: string;
        party_image_url: string;
      }[];
      bill_id: string;
      bill_name: string;
      bill_stage: string;
      bill_proposers: string;
      bill_brief_summary: string;
      bill_result: string;
    };
    approval_vote_count: number;
    total_vote_count: number;
    party_vote_list: {
      party_info: {
        party_id: number;
        party_name: string;
        party_image_url: string;
      };
      party_approval_count: number;
    }[];
  }[];
}) {
  // 본회의심사
  const [currentPage, setCurrentPage] = useState(0);
  const [itemsPerPage, setItemsPerPage] = useState(1);
  const { isOpen, onOpen, onClose } = useDisclosure();
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth >= 1024) {
        setItemsPerPage(3);
      } else if (window.innerWidth >= 768) {
        setItemsPerPage(2);
      } else {
        setItemsPerPage(1);
      }
    };

    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const startIndex = currentPage * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const currentItems = plenary_list.slice(startIndex, endIndex);

  return (
    <section className="flex flex-col gap-5">
      <div className="relative">
        <div className="bg-gray-3 dark:bg-gray-4 w-[10px] h-[10px] rounded-full border border-black absolute -left-[30px] top-4" />
        <div className="flex items-center justify-between md:w-[280px]">
          <h3 className="text-[26px] font-extralight">본회의 심사</h3>
          {plenary_list.length !== 0 && (
            <div className="flex items-center">
              <p className="text-sm font-medium text-gray-2 dark:text-gray-3">
                심의한 법안 <span className="text-black dark:text-white">{plenary_list.length}개</span>
              </p>
              <Button isIconOnly size="sm" className="w-4 h-4 p-0 bg-transparent" onClick={() => onOpen()}>
                <IconEnter />
              </Button>
              <TimelineModal isOpen={isOpen} onClose={onClose}>
                <div className="flex flex-col gap-4">
                  {plenary_list.map(({ bill_info }) => (
                    <div key={bill_info.bill_id} className="flex flex-col gap-2">
                      <p className="text-lg font-bold">{bill_info.bill_name}</p>
                      <div className="flex flex-col gap-3">
                        <div key={bill_info.bill_id} className="flex gap-[18px] items-center">
                          <Link
                            href={`/party/${bill_info.party_info[0].party_id}`}
                            className={`flex items-center justify-center w-7 h-7 rounded-full shadow-lg shrink-0 border-1.5 ${bill_info.party_info[0].party_name}`}>
                            {bill_info.party_info[0].party_name === '무소속' ? (
                              <span className="text-xs font-bold text-black dark:text-white">무</span>
                            ) : (
                              <Image
                                src={`${process.env.NEXT_PUBLIC_IMAGE_URL}${isDark ? bill_info.party_info[0].party_image_url.replace('wide', 'dark') : bill_info.party_info[0].party_image_url}`}
                                alt={`${bill_info.party_info[0].party_name} 로고 이미지`}
                                width={22}
                                height={22}
                              />
                            )}
                          </Link>
                          <div className="flex flex-col gap-1">
                            <Link href={`/bill/${bill_info.bill_id}`}>
                              <p className="text-xs font-bold">{bill_info.bill_brief_summary}</p>
                            </Link>
                            <p className="text-xs font-semibold text-gray-2 dark:text-gray-3">
                              {bill_info.bill_proposers}
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </TimelineModal>
            </div>
          )}
        </div>
      </div>
      <div>
        {plenary_list.length !== 0 ? (
          <div className="grid grid-cols-1 gap-5 md:gap-2 md:grid-cols-2 lg:grid-cols-3">
            {currentItems.map((item, index) => (
              <Card key={item.bill_info.bill_id} className="z-10 overflow-visible md:shadow-none md:border-1">
                <CardBody className="py-3 overflow-visible">
                  <Link
                    href={`/party/${item.bill_info.party_info[0].party_id}`}
                    className={`absolute -left-[39px] flex items-center justify-center w-7 h-7 rounded-full shadow-lg shrink-0 border-1.5 bg-white dark:bg-dark-b md:hidden ${item.bill_info.party_info[0].party_name}`}
                    style={index > 0 ? { top: `${index * 50}px` } : {}}>
                    {item.bill_info.party_info[0].party_name === '무소속' ? (
                      <span className="text-xs font-bold text-black dark:text-white">무</span>
                    ) : (
                      <Image
                        src={`${process.env.NEXT_PUBLIC_IMAGE_URL}${isDark ? item.bill_info.party_info[0].party_image_url.replace('wide', 'dark') : item.bill_info.party_info[0].party_image_url}`}
                        alt={`${item.bill_info.party_info[0].party_name} 로고 이미지`}
                        width={22}
                        height={22}
                      />
                    )}
                  </Link>
                  <div className="flex flex-col w-full gap-2 md:h-full md:justify-between">
                    <Link href={`/bill/${item.bill_info.bill_id}`}>
                      <p className="text-sm font-bold">{item.bill_info.bill_brief_summary}</p>
                    </Link>
                    <div className="flex items-center gap-[6px]">
                      <Chip
                        variant="bordered"
                        className="text-xs border-gray-1 dark:border-gray-2 text-gray-2 dark:text-gray-3 border-[1px]"
                        size="sm"
                        radius="sm">
                        {item.bill_info.bill_stage}
                      </Chip>
                      <p className="text-xs font-semibold text-gray-2 dark:text-gray-3">
                        {item.bill_info.bill_proposers}
                      </p>
                    </div>
                  </div>
                </CardBody>
              </Card>
            ))}
          </div>
        ) : (
          <p className="text-sm font-bold text-center">심사한 법안이 없습니다.</p>
        )}
        <Card className="w-[calc(100%-20px)] mx-auto -top-[14px] z-[5] md:hidden">
          <CardBody />
        </Card>
        <Card className="w-[calc(100%-40px)] mx-auto -top-[28px] md:hidden">
          <CardBody />
        </Card>
      </div>

      {plenary_list.length !== 0 && (
        <div className="grid grid-cols-1 gap-5 md:gap-2 md:grid-cols-2 lg:grid-cols-3">
          {currentItems.map((item) => (
            <ProcessResult
              bill_result={item.bill_info.bill_result}
              key={item.bill_info.bill_id}
              approval_count={item.approval_vote_count}
              total_vote_count={item.total_vote_count}
              party_vote_list={item.party_vote_list}
            />
          ))}
        </div>
      )}

      {plenary_list.length !== 0 && (
        <div className="flex items-center justify-between w-full md:w-[calc(100%-40px)] mx-auto">
          <Button
            isIconOnly
            size="sm"
            className="p-0 bg-transparent"
            onPress={() =>
              setCurrentPage((prev) => (prev > 0 ? prev - 1 : Math.ceil(plenary_list.length / itemsPerPage) - 1))
            }>
            <IconPrev />
          </Button>
          <Pagination
            total={Math.ceil(plenary_list.length / itemsPerPage)}
            page={currentPage + 1}
            onChange={(page) => setCurrentPage(page - 1)}
            classNames={{
              item: 'bg-gray-1 dark:bg-gray-3 text-transparent border-none shadow-none w-[6px] h-[6px]',
              cursor: 'bg-gray-3 dark:bg-gray-2 text-transparent w-[6px] h-[6px]',
            }}
          />
          <Button
            isIconOnly
            size="sm"
            className="p-0 bg-transparent"
            onPress={() =>
              setCurrentPage((prev) => (prev < Math.ceil(plenary_list.length / itemsPerPage) - 1 ? prev + 1 : 0))
            }>
            <IconNext />
          </Button>
        </div>
      )}
    </section>
  );
}
