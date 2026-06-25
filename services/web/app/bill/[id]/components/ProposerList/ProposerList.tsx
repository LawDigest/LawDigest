'use client';

import { useTheme } from 'next-themes';
import Image from 'next/image';
import Link from 'next/link';
import { Badge, Card, CardHeader, CardBody } from '@nextui-org/react';
import {
  getChairmanProposerInfo,
  getGovernmentAdministrationName,
  getPartyLogoSrc,
  isGovernmentBill,
  sortByParty,
} from '@/utils';

export default function ProposerList({
  representativeProposerList,
  publicProposerList,
  billId,
  proposerKind,
  proposerText,
  committee,
  proposeDate,
  popover,
}: {
  representativeProposerList: {
    representative_proposer_id: string;
    representative_proposer_name: string;
    represent_proposer_img_url: string;
    party_id: number;
    party_image_url: string;
    party_name: string;
  }[];
  publicProposerList: {
    public_proposer_id: string;
    public_proposer_name: string;
    public_proposer_img_url: string;
    public_proposer_party_id: number;
    public_proposer_party_image_url: string;
    public_proposer_party_name: string;
  }[];
  billId?: string | null;
  proposerKind?: string | null;
  proposerText?: string | null;
  committee?: string | null;
  proposeDate?: string | null;
  popover: boolean;
}) {
  const isGovernmentProposer = isGovernmentBill({
    proposerKind,
    billId,
    representativeProposerCount: representativeProposerList.length,
    publicProposerCount: publicProposerList.length,
  });
  const representativeProposerLength = representativeProposerList.length;
  const publicProposerLength = publicProposerList.length;
  const proposerListByParty = sortByParty({ publicProposerList });
  const { theme } = useTheme();
  const isDark = theme === 'dark';
  const chairmanProposerInfo = getChairmanProposerInfo({ proposerKind, proposerText, committee });

  if (isGovernmentProposer) {
    return (
      <Card
        classNames={{
          base: [`lg:shadow-none dark:lg:bg-dark-pb ${popover ? 'shadow-none  dark:lg:bg-transparent' : ''}`],
        }}>
        <CardHeader>
          <p className="font-medium">
            대한민국 정부{' '}
            <span className="text-sm font-normal text-gray-2">{getGovernmentAdministrationName(proposeDate)}</span>
          </p>
        </CardHeader>
        <CardBody>
          <div className="flex items-center gap-3 my-[18px]">
            <div className="flex items-center justify-center w-24 h-16 p-2 overflow-hidden bg-white border rounded-md shrink-0 dark:border-dark-l">
              <Image
                src="/images/government-logo.png"
                width={96}
                height={64}
                alt="대한민국정부 로고"
                className="object-contain w-full h-full"
              />
            </div>
            <div className="flex flex-col gap-0.5">
              <p className="text-sm font-medium">대한민국 정부</p>
              <p className="text-xs text-gray-2">{getGovernmentAdministrationName(proposeDate)}</p>
            </div>
          </div>
        </CardBody>
      </Card>
    );
  }

  if (chairmanProposerInfo) {
    return (
      <Card
        classNames={{
          base: [`lg:shadow-none dark:lg:bg-dark-pb ${popover ? 'shadow-none  dark:lg:bg-transparent' : ''}`],
        }}>
        <CardHeader>
          <p className="font-medium">
            {chairmanProposerInfo.proposerTitle}
            {chairmanProposerInfo.committeeName && (
              <span className="text-sm font-normal text-gray-2"> {chairmanProposerInfo.committeeName}</span>
            )}
          </p>
        </CardHeader>
        <CardBody>
          <div className="flex items-center gap-3 my-[18px]">
            <div className="flex items-center justify-center w-28 h-14 p-2 overflow-hidden bg-white border rounded-md shrink-0 dark:border-dark-l">
              <Image
                src={chairmanProposerInfo.logoSrc}
                width={112}
                height={56}
                alt={chairmanProposerInfo.logoAlt}
                className="object-contain w-full h-full"
              />
            </div>
            <div className="flex flex-col gap-0.5">
              <p className="text-sm font-medium">{chairmanProposerInfo.proposerTitle}</p>
              {chairmanProposerInfo.committeeName && (
                <p className="text-xs text-gray-2">{chairmanProposerInfo.committeeName}</p>
              )}
            </div>
          </div>
        </CardBody>
      </Card>
    );
  }

  return (
    <Card
      classNames={{
        base: [`lg:shadow-none dark:lg:bg-dark-pb ${popover ? 'shadow-none  dark:lg:bg-transparent' : ''}`],
      }}>
      <CardHeader>
        <p className="font-medium">
          {representativeProposerLength === 1
            ? representativeProposerList[0].representative_proposer_name
            : representativeProposerList
                .map(({ representative_proposer_name }) => representative_proposer_name)
                .join('·')}{' '}
          <span className="text-sm font-normal">{`등 ${publicProposerLength}인`}</span>
        </p>
      </CardHeader>
      <CardBody>
        <div className="flex flex-col gap-5 my-[18px]">
          {/* eslint-disable-next-line react/no-unused-prop-types */}
          {proposerListByParty.map(({ party, proposers }: { party: string; proposers: string[][] }) => (
            <div key={party} className="flex items-center gap-10">
              <Badge content={proposers.length - 1} color="danger" size="sm">
                <Link
                  href={`/party/${proposers[0][0]}`}
                  className={`flex items-center justify-center w-10 h-10 rounded-full shadow-lg shrink-0 border-1.5 ${party}`}>
                  {party === '무소속' ? (
                    <div className="text-xs font-medium text-black">무소속</div>
                  ) : (
                    <Image
                      src={getPartyLogoSrc(proposers[0][1], isDark) as string}
                      width={30}
                      height={30}
                      alt={`${party} 로고 이미지`}
                    />
                  )}
                </Link>
              </Badge>
              <div className="grid grid-cols-5 text-sm gap-x-[10px] gap-y-1">
                {proposers
                  .slice(1)
                  // eslint-disable-next-line no-nested-ternary
                  .toSorted((a, b) => (a[1] < b[1] ? -1 : a[1] > b[1] ? 1 : 0))
                  .map((proposer) => (
                    <Link href={`/congressman/${proposer[0]}`} key={proposer[0]} className="whitespace-nowrap">
                      {proposer[1].length === 2 ? (
                        <div className="flex justify-between">
                          {proposer[1].split('').map((char) => (
                            <p key={char}>{char}</p>
                          ))}
                        </div>
                      ) : (
                        proposer[1]
                      )}
                    </Link>
                  ))}
              </div>
            </div>
          ))}
        </div>
      </CardBody>
    </Card>
  );
}
