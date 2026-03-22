'use client';

import { useState, useCallback, useEffect } from 'react';
import { useTheme } from 'next-themes';
import {
  Card,
  CardHeader,
  CardBody,
  CardFooter,
  Avatar,
  Button,
  Divider,
  Tooltip,
  Chip,
  AvatarGroup,
  Popover,
  PopoverTrigger,
  PopoverContent,
} from '@nextui-org/react';
import Link from 'next/link';
import { BillProps } from '@/types';
import { IconClock, IconExport, IconScrabSmall } from '@/public/svgs';
import { usePatchBookmark } from '@/app/bill/[id]/apis';
import { getTimeRemaining, copyClipBoard } from '@/utils';
import Image from 'next/image';
import { PartyLogoReplacement } from '@/components/common';
import { getCookie } from 'cookies-next';
import { ACCESS_TOKEN } from '@/constants';
import { useSetRecoilState } from 'recoil';
import { snackbarState } from '@/store';
import { ProposerList } from '@/app/bill/[id]/components';
import GPTSummary from '../../GPTSummary';

export default function Bill({
  bill_info_dto: {
    bill_id,
    bill_name,
    brief_summary,
    propose_date,
    summary,
    gpt_summary,
    view_count,
    bill_like_count,
    bill_stage,
  },
  representative_proposer_dto_list,
  is_book_mark,
  public_proposer_dto_list,
  detail,
  viewCount,
  children,
}: BillProps) {
  const [isLiked, setIsLiked] = useState(is_book_mark);
  const [likeCount, setLikeCount] = useState(bill_like_count);
  const [isLoaded, setIsLoaded] = useState(false);
  const mutateBookmark = usePatchBookmark(bill_id);
  const [toggleMore, setToggleMore] = useState(false);
  const isRepresentativeSolo = representative_proposer_dto_list.length === 1;
  const partyName = isRepresentativeSolo ? representative_proposer_dto_list[0].party_name : '다수';
  const setSnackbar = useSetRecoilState(snackbarState);
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  const onClickToggleMore = useCallback(() => {
    setToggleMore(!toggleMore);
  }, [toggleMore]);

  const onClickScrab = useCallback(() => {
    const accessToken = getCookie(ACCESS_TOKEN);

    if (accessToken) {
      setIsLiked(!isLiked);
      setLikeCount(isLiked ? likeCount - 1 : likeCount + 1);
      setSnackbar({
        show: true,
        type: isLiked ? 'CANCEL' : 'SUCCESS',
        message: isLiked ? '해당 법안의 스크랩을 취소했습니다.' : '해당 법안을 스크랩했습니다.',
        duration: 3000,
      });

      mutateBookmark.mutate(!isLiked);
    } else {
      setSnackbar({ show: true, type: 'ERROR', message: '로그인이 필요한 서비스입니다.', duration: 3000 });
    }
  }, [isLiked, likeCount, setSnackbar]);

  const handleCopyClipBoard = useCallback(() => {
    copyClipBoard(`${process.env.NEXT_PUBLIC_DOMAIN}/bill/${bill_id}`);
    setSnackbar({ show: true, type: 'SUCCESS', message: '링크를 복사했습니다.', duration: 3000 });
  }, []);

  useEffect(() => {
    setIsLoaded(true);

    if (isLoaded) {
      const summaryElement = document.getElementById(bill_id);

      if (summaryElement !== null && summaryElement?.innerHTML !== null) {
        const markedGptSummary = gpt_summary
          .split('**')
          .map((value, index) => (index % 2 === 0 ? value : `<strong>${value}</strong>`))
          .join('');

        summaryElement.innerHTML = markedGptSummary;
      }
    }
  }, [isLoaded]);

  return (
    <section className={`flex flex-col  ${detail ? 'md:flex-row items-start' : 'md:mx-5'}`}>
      <Card
        key={bill_id}
        className="flex flex-col gap-5 px-5 pt-6 dark:bg-dark-b dark:lg:bg-dark-pb"
        radius="none"
        shadow="none">
        <CardHeader
          className={`flex  flex-col items-start gap-2 p-0  ${!detail ? 'md:w-[270px] auto md:left-0 md:absolute' : ''}`}>
          {detail && (
            <div className="flex items-center gap-1">
              <IconClock />
              <h5 className="text-sm tracking-tight text-gray-2">{getTimeRemaining(propose_date)}</h5>
            </div>
          )}

          <h2 className={`${detail ? 'text-[26px]' : 'text-xl'} font-semibold`}>{brief_summary}</h2>

          <h3 className="text-sm text-gray-2 dark:text-gray-3">{bill_name}</h3>

          {!detail && (
            <div className="flex items-center w-full gap-3">
              <h5 className="text-xs tracking-tight text-gray-3">{getTimeRemaining(propose_date)}</h5>
              <Chip
                className="text-xs bg-transparent text-gray-2 border-gray-1 dark:border-gray-3 dark:text-gray-3 border-1"
                size="sm"
                variant="bordered"
                radius="sm">
                {bill_stage}
              </Chip>
            </div>
          )}
        </CardHeader>

        <section className={!detail ? 'md:flex md:justify-between md:gap-10' : ''}>
          <div className={!detail ? 'hidden md:block md:w-[270px]' : ''} />
          <div className={!detail ? 'md:w-[440px] lg:w-[490px]' : ''}>
            <CardBody className={`p-0 leading-normal whitespace-pre-wrap ${detail ? '' : 'text-sm md:text-base'}`}>
              {/* eslint-disable-next-line jsx-a11y/click-events-have-key-events, jsx-a11y/no-noninteractive-element-interactions, no-nested-ternary */}
              <p className={detail ? '' : toggleMore ? '' : 'line-clamp-[8]'} onClick={onClickToggleMore} id={bill_id}>
                {gpt_summary && gpt_summary}
                {!gpt_summary && summary}
              </p>
              {/* eslint-disable-next-line jsx-a11y/click-events-have-key-events, jsx-a11y/no-static-element-interactions,  */}
              <span
                // eslint-disable-next-line no-nested-ternary
                className={detail ? 'hidden' : toggleMore ? 'hidden' : 'text-gray-2 dark:text-gray-3'}
                onClick={onClickToggleMore}>
                더 보기
              </span>
            </CardBody>

            {!detail && (
              <CardFooter className="flex items-center justify-between p-0 mt-5 -ml-1">
                <div className="flex gap-2">
                  <div className="flex items-center text-sm text-gray-3">
                    <Button isIconOnly size="sm" className="p-0 bg-transparent" onClick={onClickScrab}>
                      <IconScrabSmall isActive={isLiked} />
                    </Button>
                    <h4 className="mr-2">스크랩</h4>
                    <h4>{likeCount}</h4>
                  </div>
                  <div className="flex items-center text-sm text-gray-3">
                    <h4 className="mr-2">조회수</h4>
                    <h4>{view_count}</h4>
                  </div>
                  <Tooltip content="링크 복사하기" className="dark:text-white">
                    <Button
                      isIconOnly
                      size="sm"
                      className="bg-transparent"
                      aria-label="Export Button"
                      onClick={handleCopyClipBoard}>
                      <IconExport />
                    </Button>
                  </Tooltip>
                </div>

                <Link href={`/bill/${bill_id}`}>
                  <Button
                    className="text-sm font-medium bg-gray-1 dark:bg-gray-3 text-gray-3 dark:text-gray-2 w-[88px] h-8"
                    size="sm"
                    variant="flat">
                    자세히 보기
                  </Button>
                </Link>
              </CardFooter>
            )}

            {detail && (
              <CardFooter className="flex items-center justify-between p-0 mt-10">
                <div className="flex gap-4">
                  <div className="flex items-center text-sm text-gray-2">
                    <Button isIconOnly size="sm" className="p-0 bg-transparent" onClick={onClickScrab}>
                      <IconScrabSmall isActive={isLiked} />
                    </Button>
                    <h4 className="mr-2">스크랩</h4>
                    <h4>{likeCount}</h4>
                  </div>
                  <div className="flex items-center text-sm text-gray-2">
                    <h4 className="mr-2">조회수</h4>
                    <h4>{viewCount}</h4>
                  </div>
                </div>
                <Tooltip content="링크 복사하기">
                  <Button isIconOnly size="sm" className="bg-transparent" onClick={handleCopyClipBoard}>
                    <IconExport />
                  </Button>
                </Tooltip>
              </CardFooter>
            )}
          </div>
        </section>

        {detail && (
          <div className="flex flex-col gap-[34px]">
            <Divider className="bg-gray-0.5 dark:bg-dark-l md:hidden" />

            <GPTSummary />

            <div className="flex flex-col items-center gap-3">
              <h5 className="text-xs font-semibold text-theme-alert">
                AI 기반의 요약은 내용이 불완전할 수 있습니다. 꼭 원문을 확인해주세요 !
              </h5>

              <Link href={`https://likms.assembly.go.kr/bill/billDetail.do?billId=${bill_id}`}>
                <Button
                  size="lg"
                  color="primary"
                  radius="full"
                  className="w-[242px] h-[56px] bg-primary-3 dark:bg-gray-0.5 dark:text-black">
                  원문 확인하기
                </Button>
              </Link>
            </div>

            <Divider className="bg-gray-0.5 dark:bg-dark-l md:hidden" />
          </div>
        )}
      </Card>

      <div
        className={`flex flex-col w-full md:w-auto md:flex-col ${detail ? 'md:border-l md:dark:border-dark-l' : ''}`}>
        <div className="pt-4 pb-6">
          <Card
            className={`flex flex-row h-[78px] mx-5 border-1.5 items-center justify-between px-[18px] dark:bg-gray-4 md:w-[410px] lg:max-w-full lg:w-[490px] md:float-right ${detail ? 'md:w-[300px] lg:float-left' : ''} ${partyName}`}
            radius="sm"
            shadow="sm">
            <div className="flex items-center gap-2">
              {isRepresentativeSolo && (
                <Link
                  href={
                    isRepresentativeSolo
                      ? `/congressman/${representative_proposer_dto_list[0].representative_proposer_id}`
                      : {}
                  }
                  scroll={isRepresentativeSolo}
                  onClick={(e) => {
                    if (!isRepresentativeSolo) e.preventDefault();
                  }}>
                  <Avatar
                    radius="full"
                    src={`${process.env.NEXT_PUBLIC_IMAGE_URL}${representative_proposer_dto_list[0].represent_proposer_img_url}`}
                    className="border dark:border-dark-l"
                  />
                </Link>
              )}
              <div className="flex flex-col gap-0.5">
                <Link
                  href={
                    isRepresentativeSolo
                      ? `/congressman/${representative_proposer_dto_list[0].representative_proposer_id}`
                      : {}
                  }
                  scroll={isRepresentativeSolo}
                  onClick={(e) => {
                    if (!isRepresentativeSolo) e.preventDefault();
                  }}>
                  <h3 className="font-medium">
                    {isRepresentativeSolo
                      ? `${representative_proposer_dto_list[0].representative_proposer_name} 의원`
                      : `${representative_proposer_dto_list.map(({ representative_proposer_name }) => representative_proposer_name).join('·')} 의원`}
                  </h3>
                </Link>

                <Popover placement="bottom" showArrow>
                  <PopoverTrigger>
                    <Button className="p-0 m-0 bg-transparent h-min">
                      <Tooltip showArrow content="발의자 명단 보기">
                        <h4 className="text-xs text-gray-2">
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
            </div>

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
                    width={100}
                    height={45}
                    alt={`${representative_proposer_dto_list[0].party_name} 이미지`}
                    className="w-[100px] h-[40px] object-contain"
                  />
                ) : (
                  <PartyLogoReplacement partyName={representative_proposer_dto_list[0].party_name} circle={false} />
                )}
              </Link>
            ) : (
              <AvatarGroup>
                {representative_proposer_dto_list.map(({ party_image_url, party_id, party_name }) => (
                  <Link href={party_image_url !== null ? `/party/${party_id}` : {}} key={party_id}>
                    <Avatar
                      src={`${process.env.NEXT_PUBLIC_IMAGE_URL}${isDark ? party_image_url.replace('wide', 'dark') : party_image_url}`}
                      size="md"
                      classNames={{
                        base: [`bg-white dark:bg-dark-pb p-1 border ${party_name}`],
                        img: ['object-contain'],
                      }}
                    />
                  </Link>
                ))}
              </AvatarGroup>
            )}
          </Card>
        </div>

        <section className="h-full mx-5">{children}</section>
      </div>

      {!detail && <Divider className="h-[10px] md:h-[1px] bg-gray-0.5 dark:bg-gray-4" />}
    </section>
  );
}
