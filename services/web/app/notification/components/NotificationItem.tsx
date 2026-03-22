'use client';

import { useTheme } from 'next-themes';
import Link from 'next/link';
import getTimeRemaining from '@/utils/getTimeRemaining';
import type { Notification } from '@/types';
import { Avatar, AvatarGroup, Button, Dropdown, DropdownTrigger, DropdownMenu, DropdownItem } from '@nextui-org/react';
import { IconAlert, IconKebab } from '@/public/svgs';

export default function NotificationItem({
  title,
  content,
  created_date,
  type,
  notification_image_url_list,
  target,
  read,
  notification_id,
  onClickRead,
  onClickDelete,
}: Notification & {
  onClickRead: (notificationId: number, isClickByButton: boolean) => void;
  onClickDelete: (notificationId: number) => void;
}) {
  const { theme } = useTheme();
  const isDark = theme === 'dark';
  const isRepresentativeSolo = notification_image_url_list.length === 1;
  const imageUrlList = notification_image_url_list.map((str) => str.split(':'));
  // eslint-disable-next-line no-constant-condition
  const linkUrl = `${type === 'congressman_party_update' ? 'congressman' : 'bill'}/${target}`;

  return (
    <section className="flex items-center gap-[10px] lg:gap-4">
      <div className="flex items-center gap-1">
        <div className={read ? 'invisible' : ''}>
          <IconAlert />
        </div>

        {isRepresentativeSolo ? (
          <Avatar
            radius="full"
            src={`${process.env.NEXT_PUBLIC_IMAGE_URL}${!isDark ? imageUrlList[0][1] : imageUrlList[0][1].replace('wide', 'dark')}`}
            size="md"
            className="w-[50px] h-[50px]"
            classNames={{
              base: [
                // eslint-disable-next-line no-constant-condition
                `${type === 'bill_stage_update' || type === 'bill_result_update' ? 'bg-white dark:bg-dark-pb p-1' : ''} border ${imageUrlList[0][0]}`,
              ],
              // eslint-disable-next-line no-constant-condition
              img: [`${type === 'bill_stage_update' || type === 'bill_result_update' ? 'object-contain' : ''}`],
            }}
          />
        ) : (
          <AvatarGroup className={`w-[50px] ${imageUrlList.length >= 3 ? 'gap-0' : ''}`} isGrid max={3}>
            {imageUrlList.map((notification_image_url) => (
              <Avatar
                key={notification_image_url[0]}
                src={`${process.env.NEXT_PUBLIC_IMAGE_URL}${!isDark ? notification_image_url[1] : notification_image_url[1].replace('wide', 'dark')}`}
                size="sm"
                classNames={{
                  base: [`shrink-0 bg-white dark:bg-dark-pb p-1 border ${notification_image_url[0]}`],
                  img: ['object-contain'],
                }}
              />
            ))}
          </AvatarGroup>
        )}
      </div>

      <div className="flex items-center justify-between w-full">
        <div className="flex flex-col w-full gap-1">
          <Link href={linkUrl} onClick={() => onClickRead(notification_id, false)}>
            <p className="text-xs font-bold md:text-base ">
              {title} &nbsp;
              <span className="text-[10px] md:text-sm font-medium text-gray-2 dark:text-gray-3">
                {getTimeRemaining(created_date)}
              </span>
            </p>
          </Link>
          <p className="text-gray-3 dark:text-gray-2 text-[10px] md:text-sm">{content}</p>
        </div>

        <Dropdown>
          <DropdownTrigger>
            <Button isIconOnly size="sm" className="bg-transparent">
              <IconKebab isPassed />
            </Button>
          </DropdownTrigger>
          <DropdownMenu>
            <DropdownItem onClick={() => onClickRead(notification_id, true)}>읽음 표시</DropdownItem>
            <DropdownItem onClick={() => onClickDelete(notification_id)}>삭제</DropdownItem>
          </DropdownMenu>
        </Dropdown>
      </div>
    </section>
  );
}
