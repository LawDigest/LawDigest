'use client';

import { useTheme } from 'next-themes';
import Image from 'next/image';
import { BillProps } from '@/types';
import {
  Card,
  CardFooter,
  CardBody,
  Chip,
  AvatarGroup,
  Avatar,
  Popover,
  PopoverTrigger,
  PopoverContent,
  Tooltip,
  Button,
} from '@nextui-org/react';
import Link from 'next/link';
import { PartyLogoReplacement } from '@/components';
import { ProposerList } from '@/app/bill/[id]/components';

export default function BillBookmarked({
  bill_info_dto: { bill_id, brief_summary, bill_stage },
  representative_proposer_dto_list,
  public_proposer_dto_list,
}: BillProps) {
  const isRepresentativeSolo = representative_proposer_dto_list.length === 1;
  const partyName = isRepresentativeSolo ? representative_proposer_dto_list[0].party_name : '다수';
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  return (
    <Card className={`border-1.5 flex-row md:py-2 ${partyName}`} radius="md">
      <CardBody className="flex justify-between gap-2">
        <Link href={`/bill/${bill_id}`}>
          <p className="text-sm font-bold md:text-base lg:text-lg">{brief_summary}</p>
        </Link>
        <div className="flex flex-wrap items-center w-full gap-2 overflow-visible">
          <Chip
            className="text-xs bg-transparent md:text-sm text-gray-2 border-gray-1 dark:border-gray-3 dark:text-gray-3 border-1"
            size="sm"
            variant="bordered"
            radius="sm">
            {bill_stage}
          </Chip>
          <Popover placement="bottom" showArrow>
            <PopoverTrigger>
              <Button className="p-0 m-0 bg-transparent h-min">
                <Tooltip showArrow content="발의자 명단 보기">
                  <h4 className="text-xs font-semibold md:text-sm text-gray-2 shrink-0">
                    {isRepresentativeSolo
                      ? `${representative_proposer_dto_list[0].representative_proposer_name} 의원 등 ${public_proposer_dto_list.length}인`
                      : `${representative_proposer_dto_list
                          .map(({ representative_proposer_name }) => representative_proposer_name)
                          .join('·')} 의원 등 ${public_proposer_dto_list.length}인`}
                  </h4>
                </Tooltip>
              </Button>
            </PopoverTrigger>
            <PopoverContent>
              <ProposerList
                representativeProposerList={representative_proposer_dto_list}
                publicProposerList={public_proposer_dto_list}
                popover
              />
            </PopoverContent>
          </Popover>
        </div>
      </CardBody>
      <CardFooter className="flex justify-center pl-0 overflow-visible basis-1/4 md:basis-1/5 shrink-0">
        {/* eslint-disable-next-line no-nested-ternary */}
        {isRepresentativeSolo ? (
          <Link
            href={
              representative_proposer_dto_list[0].party_image_url !== null
                ? `/party/${representative_proposer_dto_list[0].party_id}`
                : {}
            }
            onClick={(e) => {
              if (representative_proposer_dto_list[0].party_image_url === null) e.preventDefault();
            }}>
            {representative_proposer_dto_list[0].party_image_url !== null ? (
              <Image
                src={`${process.env.NEXT_PUBLIC_IMAGE_URL}${isDark ? representative_proposer_dto_list[0].party_image_url.replace('wide', 'dark') : representative_proposer_dto_list[0].party_image_url}`}
                width={60}
                height={30}
                alt={`${representative_proposer_dto_list[0].party_name} 이미지`}
                className="object-contain w-[60px] h-[30px] md:w-[90px] md:h-[45px]"
              />
            ) : (
              <PartyLogoReplacement partyName={representative_proposer_dto_list[0].party_name} circle={false} />
            )}
          </Link>
        ) : (
          <AvatarGroup>
            {representative_proposer_dto_list.map(({ party_image_url, party_id, party_name }) => (
              <Link href={`/party/${party_id}`} key={party_id}>
                <Avatar
                  src={`${process.env.NEXT_PUBLIC_IMAGE_URL}${isDark ? party_image_url.replace('wide', 'dark') : party_image_url}`}
                  size="md"
                  classNames={{
                    base: [`bg-white dark:bg-dark-l p-1 border ${party_name}`],
                    img: ['object-contain'],
                  }}
                />
              </Link>
            ))}
          </AvatarGroup>
        )}
      </CardFooter>
    </Card>
  );
}
