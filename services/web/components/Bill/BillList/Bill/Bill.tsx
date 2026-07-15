'use client';

import type { CSSProperties, KeyboardEvent, ReactNode } from 'react';
import { useState, useCallback } from 'react';
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
} from '@heroui/react';
import Link from 'next/link';
import { BillProps } from '@/types';
import { IconClock, IconExport, IconScrabSmall } from '@/public/svgs';
import { usePatchBookmark } from '@/app/bill/[id]/apis';
import {
  getTimeRemaining,
  copyClipBoard,
  getPartyLogoSrc,
  getGovernmentAdministrationName,
  isGovernmentBill,
  getChairmanProposerInfo,
} from '@/utils';
import Image from 'next/image';
import { PartyLogoReplacement } from '@/components/common';
import { getCookie } from 'cookies-next';
import { ACCESS_TOKEN } from '@/constants';
import { useSetAtom } from 'jotai';
import { snackbarState } from '@/store';
import { ProposerList } from '@/app/bill/[id]/components';
import GPTSummary from '../../GPTSummary';
import {
  getFeedSummaryMarkdown,
  getPartyAccentColor,
  getSummaryVisibilityClassNames,
} from './renderBillSummaryMarkdown';
import SafeBillSummaryHtml from './SafeBillSummaryHtml';

export default function Bill({
  bill_info_dto: {
    bill_id,
    bill_name,
    title,
    propose_date,
    summary,
    gpt_summary,
    view_count,
    bill_like_count,
    bill_stage,
    proposer_kind,
    proposers,
    committee,
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
  const mutateBookmark = usePatchBookmark(bill_id);
  const [toggleMore, setToggleMore] = useState(false);
  const isGovernmentProposer = isGovernmentBill({
    proposerKind: proposer_kind,
    billId: bill_id,
    representativeProposerCount: representative_proposer_dto_list.length,
    publicProposerCount: public_proposer_dto_list.length,
  });
  const chairmanProposerInfo = getChairmanProposerInfo({
    proposerKind: proposer_kind,
    proposerText: proposers,
    committee,
  });
  const isChairmanProposer = chairmanProposerInfo !== null;
  const isRepresentativeSolo =
    !isGovernmentProposer && !isChairmanProposer && representative_proposer_dto_list.length === 1;
  const partyName = isRepresentativeSolo ? representative_proposer_dto_list[0].party_name : '다수';
  let proposerCardBorderClassName = partyName;
  if (isGovernmentProposer) {
    proposerCardBorderClassName = 'lawdigest-government-proposer-card';
  } else if (isChairmanProposer) {
    proposerCardBorderClassName = 'lawdigest-chairman-proposer-card';
  }
  const setSnackbar = useSetAtom(snackbarState);
  const { theme } = useTheme();
  const isDark = theme === 'dark';
  const displayedSummary = gpt_summary && !detail ? getFeedSummaryMarkdown(gpt_summary) : gpt_summary || summary;
  const { moreButtonClassName, summaryClassName } = getSummaryVisibilityClassNames({
    detail: Boolean(detail),
    expanded: toggleMore,
  });
  const summaryAccentStyle = {
    '--lawdigest-summary-accent': isGovernmentProposer
      ? '#c60c30'
      : chairmanProposerInfo?.accentColor ?? getPartyAccentColor(partyName),
    '--lawdigest-summary-accent-secondary': isGovernmentProposer
      ? '#003478'
      : chairmanProposerInfo?.accentColor ?? getPartyAccentColor(partyName),
  } as CSSProperties;
  const summaryContentClassName =
    `${summaryClassName} ${isGovernmentProposer ? 'lawdigest-summary-government-accent' : ''}`.trim();

  const onClickToggleMore = useCallback(() => {
    setToggleMore(!toggleMore);
  }, [toggleMore]);

  const onKeyDownToggleMore = useCallback(
    (event: KeyboardEvent<HTMLDivElement | HTMLSpanElement>) => {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        onClickToggleMore();
      }
    },
    [onClickToggleMore],
  );

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

  let proposerAffiliationContent = (
    <AvatarGroup>
      {representative_proposer_dto_list.map(({ party_image_url, party_id, party_name }) => (
        <Link href={party_image_url !== null ? `/party/${party_id}` : {}} key={party_id}>
          <Avatar
            src={getPartyLogoSrc(party_image_url, isDark) ?? undefined}
            size="md"
            classNames={{
              base: [`bg-white dark:bg-dark-pb p-1 border ${party_name}`],
              img: ['object-contain'],
            }}
          />
        </Link>
      ))}
    </AvatarGroup>
  );

  if (isGovernmentProposer) {
    proposerAffiliationContent = (
      <Image
        src="/images/government-logo.png"
        width={320}
        height={245}
        alt="대한민국정부 로고"
        className="w-auto h-[60px] object-contain -my-1"
      />
    );
  } else if (chairmanProposerInfo) {
    proposerAffiliationContent = (
      <Image
        src={chairmanProposerInfo.logoSrc}
        width={280}
        height={72}
        alt={chairmanProposerInfo.logoAlt}
        className="w-auto h-[34px] max-w-[150px] object-contain"
      />
    );
  } else if (isRepresentativeSolo) {
    proposerAffiliationContent = (
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
            src={getPartyLogoSrc(representative_proposer_dto_list[0].party_image_url, isDark) as string}
            width={100}
            height={45}
            alt={`${representative_proposer_dto_list[0].party_name} 이미지`}
            className="w-[100px] h-[40px] object-contain"
          />
        ) : (
          <PartyLogoReplacement partyName={representative_proposer_dto_list[0].party_name} circle={false} />
        )}
      </Link>
    );
  }

  let proposerIdentityContent: ReactNode = (
    <>
      <Link
        href={
          isRepresentativeSolo ? `/congressman/${representative_proposer_dto_list[0].representative_proposer_id}` : {}
        }
        scroll={isRepresentativeSolo}
        onClick={(e) => {
          if (!isRepresentativeSolo) e.preventDefault();
        }}>
        <h3 className="font-medium">
          {isRepresentativeSolo
            ? `${representative_proposer_dto_list[0].representative_proposer_name} 의원`
            : `${representative_proposer_dto_list
                .map(({ representative_proposer_name }) => representative_proposer_name)
                .join('·')} 의원`}
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
            billId={bill_id}
            proposerKind={proposer_kind}
            proposerText={proposers}
            committee={committee}
            proposeDate={propose_date}
            popover
          />
        </PopoverContent>
      </Popover>
    </>
  );

  if (isGovernmentProposer) {
    proposerIdentityContent = (
      <>
        <h3 className="font-medium">대한민국 정부</h3>
        <h4 className="text-xs text-gray-2">{getGovernmentAdministrationName(propose_date)}</h4>
      </>
    );
  } else if (chairmanProposerInfo) {
    proposerIdentityContent = (
      <>
        <h3 className="font-medium">{chairmanProposerInfo.proposerTitle}</h3>
        {chairmanProposerInfo.committeeName && (
          <h4 className="text-xs text-gray-2">{chairmanProposerInfo.committeeName}</h4>
        )}
      </>
    );
  }

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

          <h2 className={`${detail ? 'text-[26px]' : 'text-xl'} font-semibold`}>{title}</h2>

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
              <SafeBillSummaryHtml
                className={summaryContentClassName}
                style={summaryAccentStyle}
                onClick={onClickToggleMore}
                onKeyDown={onKeyDownToggleMore}
                ariaLabel={toggleMore ? '법안 요약 접기' : '법안 요약 더 보기'}
                markdown={displayedSummary}
              />
              <span
                className={moreButtonClassName}
                onClick={onClickToggleMore}
                onKeyDown={onKeyDownToggleMore}
                role="button"
                tabIndex={0}>
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
            className={`flex flex-row h-[78px] mx-5 border-1.5 items-center justify-between px-[18px] dark:bg-gray-4 md:w-[410px] lg:max-w-full lg:w-[490px] md:float-right ${detail ? 'md:w-[300px] lg:float-left' : ''} ${proposerCardBorderClassName}`}
            radius="sm"
            shadow="sm">
            <div className="flex items-center gap-2">
              {!isGovernmentProposer && isRepresentativeSolo && (
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
                    name={representative_proposer_dto_list[0].representative_proposer_name}
                    src={`${process.env.NEXT_PUBLIC_IMAGE_URL}${representative_proposer_dto_list[0].represent_proposer_img_url}`}
                    className="border dark:border-dark-l"
                  />
                </Link>
              )}
              <div className="flex flex-col gap-0.5">{proposerIdentityContent}</div>
            </div>

            {proposerAffiliationContent}
          </Card>
        </div>

        <section className="h-full mx-5">{children}</section>
      </div>

      {!detail && <Divider className="h-[10px] md:h-[1px] bg-gray-0.5 dark:bg-gray-4" />}
    </section>
  );
}
