'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { useTheme } from 'next-themes';
import { Card, CardBody, CardHeader, Pagination, Button, useDisclosure } from '@nextui-org/react';
import { IconEnter, IconNext, IconPrev } from '@/public/svgs';
import TimelineModal from './TimelineModal';

export default function CommitteeAuditList({
  committee_audit_list,
}: {
  committee_audit_list: {
    committee_name: string;
    bill_count: number;
    bill_outline_dto_list: {
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
    }[];
  }[];
}) {
  // 위원회심사
  const [currentPage, setCurrentPage] = useState(0);
  const [itemsPerPage, setItemsPerPage] = useState(1);
  const { isOpen: isOpenIndividual, onOpen: onOpenIndividual, onClose: onCloseIndividual } = useDisclosure();
  const { isOpen: isOpenAll, onOpen: onOpenAll, onClose: onCloseAll } = useDisclosure();
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
  const currentItems = committee_audit_list.slice(startIndex, endIndex);

  return (
    <section className="flex flex-col gap-5">
      <div className="relative">
        <div className="bg-gray-3 dark:bg-gray-4 w-[10px] h-[10px] rounded-full border border-black absolute -left-[30px] top-4" />
        <div className="flex items-center justify-between md:w-[280px]">
          <h3 className="text-[26px] font-extralight">위원회 심사</h3>
          {committee_audit_list.length !== 0 && (
            <div className="flex items-center">
              <p className="text-sm font-medium text-gray-2 dark:text-gray-3">
                심의한 법안{' '}
                <span className="text-black dark:text-white">
                  {committee_audit_list.reduce((pre, cur) => pre + cur.bill_outline_dto_list.length, 0)}개
                </span>
              </p>
              <Button isIconOnly size="sm" className="w-4 h-4 p-0 bg-transparent" onClick={() => onOpenAll()}>
                <IconEnter />
              </Button>
              <TimelineModal isOpen={isOpenAll} onClose={onCloseAll}>
                <div className="flex flex-col gap-4">
                  {committee_audit_list.map(({ committee_name, bill_outline_dto_list }) => (
                    <div key={committee_name} className="flex flex-col gap-2">
                      <p className="text-lg font-bold">{committee_name}</p>
                      <div className="flex flex-col gap-3">
                        {bill_outline_dto_list.map(({ party_info, bill_id, bill_proposers, bill_brief_summary }) => (
                          <div key={bill_id} className="flex gap-[18px] items-center">
                            <Link
                              href={`/party/${party_info[0].party_id}`}
                              className={`flex items-center justify-center w-7 h-7 rounded-full shadow-lg shrink-0 border-1.5 ${party_info[0].party_name}`}>
                              {party_info[0].party_name === '무소속' ? (
                                <span className="text-xs font-bold text-black dark:text-white">무</span>
                              ) : (
                                <Image
                                  src={`${process.env.NEXT_PUBLIC_IMAGE_URL}${isDark ? party_info[0].party_image_url.replace('wide', 'dark') : party_info[0].party_image_url}`}
                                  alt={`${party_info[0].party_name} 로고 이미지`}
                                  width={22}
                                  height={22}
                                />
                              )}
                            </Link>
                            <div className="flex flex-col gap-1">
                              <Link href={`/bill/${bill_id}`}>
                                <p className="text-xs font-bold">{bill_brief_summary}</p>
                              </Link>
                              <p className="text-xs font-semibold text-gray-2 dark:text-gray-3">{bill_proposers}</p>
                            </div>
                          </div>
                        ))}
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
        <div className="grid grid-cols-1 gap-5 md:gap-2 md:grid-cols-2 lg:grid-cols-3">
          {currentItems.map((item) => (
            <Card key={item.committee_name} className="z-10 px-2 md:shadow-none md:border-1">
              {committee_audit_list.length !== 0 && (
                <CardHeader>
                  <p className="text-[22px] font-bold">{item.committee_name}</p>
                </CardHeader>
              )}
              <CardBody>
                {committee_audit_list.length !== 0 ? (
                  <div className="flex flex-col w-full gap-5">
                    <div className="flex items-center">
                      <p className="text-xs font-medium text-gray-2 dark:text-gray-3">
                        심사한 법안 <span className="text-black dark:text-white">{item.bill_count}개</span>
                      </p>
                      <Button
                        isIconOnly
                        size="sm"
                        className="w-4 h-4 p-0 bg-transparent"
                        onClick={() => onOpenIndividual()}>
                        <IconEnter />
                      </Button>
                      <TimelineModal isOpen={isOpenIndividual} onClose={onCloseIndividual}>
                        <div className="flex flex-col gap-3">
                          {item.bill_outline_dto_list.map(
                            ({ party_info, bill_id, bill_proposers, bill_brief_summary }) => (
                              <div key={bill_id} className="flex gap-[18px] items-center">
                                <Link
                                  href={`/party/${party_info[0].party_id}`}
                                  className={`flex items-center justify-center w-7 h-7 rounded-full shadow-lg shrink-0 border-1.5 ${party_info[0].party_name}`}>
                                  {party_info[0].party_name === '무소속' ? (
                                    <span className="text-xs font-bold text-black dark:text-white">무</span>
                                  ) : (
                                    <Image
                                      src={`${process.env.NEXT_PUBLIC_IMAGE_URL}${isDark ? party_info[0].party_image_url.replace('wide', 'dark') : party_info[0].party_image_url}`}
                                      alt={`${party_info[0].party_name} 로고 이미지`}
                                      width={22}
                                      height={22}
                                    />
                                  )}
                                </Link>
                                <div className="flex flex-col gap-1">
                                  <Link href={`/bill/${bill_id}`}>
                                    <p className="text-xs font-bold">{bill_brief_summary}</p>
                                  </Link>
                                  <p className="text-xs font-semibold text-gray-2 dark:text-gray-3">{bill_proposers}</p>
                                </div>
                              </div>
                            ),
                          )}
                        </div>
                      </TimelineModal>
                    </div>
                    <div className="flex flex-col gap-3">
                      {item.bill_outline_dto_list
                        .slice(0, 5)
                        .map(({ party_info, bill_id, bill_proposers, bill_brief_summary }) => (
                          <div key={bill_id} className="flex gap-[18px] items-center">
                            <Link
                              href={`/party/${party_info[0].party_id}`}
                              className={`flex items-center justify-center w-7 h-7 rounded-full shadow-lg shrink-0 border-1.5 ${party_info[0].party_name}`}>
                              {party_info[0].party_name === '무소속' ? (
                                <span className="text-xs font-bold text-black dark:text-white">무</span>
                              ) : (
                                <Image
                                  src={`${process.env.NEXT_PUBLIC_IMAGE_URL}${isDark ? party_info[0].party_image_url.replace('wide', 'dark') : party_info[0].party_image_url}`}
                                  alt={`${party_info[0].party_name} 로고 이미지`}
                                  width={22}
                                  height={22}
                                />
                              )}
                            </Link>
                            <div className="flex flex-col gap-1">
                              <Link href={`/bill/${bill_id}`}>
                                <p className="text-xs font-bold">{bill_brief_summary}</p>
                              </Link>
                              <p className="text-xs font-semibold text-gray-2 dark:text-gray-3">{bill_proposers}</p>
                            </div>
                          </div>
                        ))}
                    </div>
                  </div>
                ) : (
                  <p className="text-sm font-bold text-center">심사한 법안이 없습니다.</p>
                )}
              </CardBody>
            </Card>
          ))}
        </div>
        <Card className="w-[calc(100%-20px)] mx-auto -top-[14px] z-[5] md:hidden">
          <CardBody />
        </Card>
        <Card className="w-[calc(100%-40px)] mx-auto -top-[28px] md:hidden">
          <CardBody />
        </Card>
      </div>

      {committee_audit_list.length !== 0 && (
        <div className="flex items-center justify-between">
          <Button
            isIconOnly
            size="sm"
            className="p-0 bg-transparent"
            onPress={() =>
              setCurrentPage((prev) => (prev > 0 ? prev - 1 : committee_audit_list.length / itemsPerPage - 1))
            }>
            <IconPrev />
          </Button>
          <Pagination
            total={Math.ceil(committee_audit_list.length / itemsPerPage)}
            page={currentPage + 1}
            onChange={(page) => setCurrentPage(page - 1)}
            classNames={{
              item: 'bg-gray-1 text-transparent border-none shadow-none w-[6px] h-[6px]',
              cursor: 'bg-gray-3 text-transparent w-[6px] h-[6px]',
            }}
          />
          <Button
            isIconOnly
            size="sm"
            className="p-0 bg-transparent"
            onPress={() =>
              setCurrentPage((prev) =>
                prev < Math.ceil(committee_audit_list.length / itemsPerPage) - 1 ? prev + 1 : 0,
              )
            }>
            <IconNext />
          </Button>
        </div>
      )}
    </section>
  );
}
