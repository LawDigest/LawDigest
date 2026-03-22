'use client';

import { useTheme } from 'next-themes';
import Image from 'next/image';
import Link from 'next/link';
import { Badge, Card, CardHeader, CardBody } from '@nextui-org/react';
import { sortByParty } from '@/utils';

export default function ProposerList({
  representativeProposerList,
  publicProposerList,
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
  popover: boolean;
}) {
  const representativeProposerLength = representativeProposerList.length;
  const publicProposerLength = publicProposerList.length;
  const proposerListByParty = sortByParty({ publicProposerList });
  const { theme } = useTheme();
  const isDark = theme === 'dark';

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
                      src={`${process.env.NEXT_PUBLIC_IMAGE_URL}${isDark ? proposers[0][1].replace('wide', 'dark') : proposers[0][1]}`}
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
