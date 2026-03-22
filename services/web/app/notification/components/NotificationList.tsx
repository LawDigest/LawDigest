'use client';

import { useState, useEffect, useCallback } from 'react';
import { getDateStatus } from '@/utils';
import { Divider, Button, Dropdown, DropdownTrigger, DropdownMenu, DropdownItem } from '@nextui-org/react';
import { IconKebab } from '@/public/svgs';
import { useSetRecoilState } from 'recoil';
import { snackbarState } from '@/store';
import {
  useGetNotificationCount,
  useGetNotification,
  usePutNotificationRead,
  usePutNotificationReadAll,
  useDeleteNotification,
  useDeleteNotificationAll,
} from '../apis';
import NotificationItem from './NotificationItem';

const initialData = [
  [
    {
      title: '',
      notification_id: 0,
      content: '',
      target: '',
      type: '',
      extra: '',
      created_date: '',
      notification_image_url_list: [''],
      read: false,
    },
  ],
  [
    {
      title: '',
      notification_id: 0,
      content: '',
      target: '',
      type: '',
      extra: '',
      created_date: '',
      notification_image_url_list: [''],
      read: false,
    },
  ],
  [
    {
      title: '',
      notification_id: 0,
      content: '',
      target: '',
      type: '',
      extra: '',
      created_date: '',
      notification_image_url_list: [''],
      read: false,
    },
  ],
];

export default function NotificationList() {
  const { data: notificationCount } = useGetNotificationCount();
  const { data: notifications } = useGetNotification();
  const setSnackbar = useSetRecoilState(snackbarState);
  const mutateRead = usePutNotificationRead();
  const mutateDelete = useDeleteNotification();
  const mutateReadAll = usePutNotificationReadAll();
  const mutateDeleteAll = useDeleteNotificationAll();
  const [listByDateStatus, setListByDateStatus] = useState(() =>
    notifications
      ? Array.from(Array(3), (v, i) =>
          // eslint-disable-next-line no-nested-ternary
          i === 0
            ? notifications.filter((notification) => getDateStatus(notification.created_date) === '지난 한 주')
            : i === 1
              ? notifications.filter((notification) => getDateStatus(notification.created_date) === '지난 한 달')
              : notifications.filter((notification) => getDateStatus(notification.created_date) === '지난 알림'),
        )
      : initialData,
  );

  useEffect(() => {
    if (notifications) {
      setListByDateStatus(
        Array.from(Array(3), (v, i) =>
          // eslint-disable-next-line no-nested-ternary
          i === 0
            ? notifications.filter((notification) => getDateStatus(notification.created_date) === '지난 한 주')
            : i === 1
              ? notifications.filter((notification) => getDateStatus(notification.created_date) === '지난 한 달')
              : notifications.filter((notification) => getDateStatus(notification.created_date) === '지난 알림'),
        ),
      );
    }
  }, [notifications]);

  const onClickRead = useCallback(
    (notificationId: number, isClickByButton: boolean) => {
      mutateRead.mutate(notificationId);
      if (isClickByButton) {
        setSnackbar({
          show: true,
          type: 'SUCCESS',
          message: '해당 알림을 읽었습니다.',
          duration: 3000,
        });
      }
    },
    [mutateRead],
  );

  const onClickDelete = useCallback(
    (notificationId: number) => {
      mutateDelete.mutate(notificationId);
      setSnackbar({
        show: true,
        type: 'CANCEL',
        message: '해당 알림을 삭제했습니다.',
        duration: 3000,
      });
    },
    [mutateDelete],
  );

  const onClickReadAll = useCallback(() => {
    mutateReadAll.mutate();
    setSnackbar({
      show: true,
      type: 'SUCCESS',
      message: '알림을 모두 읽었습니다.',
      duration: 3000,
    });
  }, [mutateReadAll]);

  const onClickDeleteAll = useCallback(() => {
    mutateDeleteAll.mutate();
    setSnackbar({
      show: true,
      type: 'CANCEL',
      message: '알림을 모두 삭제했습니다.',
      duration: 3000,
    });
  }, [mutateDeleteAll]);

  return (
    <section className="flex flex-col px-5 mt-6 mb-10">
      <div className="mb-[18px] ml-3">
        <div className="flex justify-between items-center">
          {notificationCount?.notification_count === 0 ? (
            <p className="text-sm md:text-base text-gray-2 dark:text-gray-3">알림이 없습니다.</p>
          ) : (
            <p className="text-sm md:text-base text-gray-2 dark:text-gray-3">
              <span className="text-black dark:text-gray-2">{notificationCount?.notification_count}개</span>의 읽지 않은
              알림이 있습니다.
            </p>
          )}
          <Dropdown>
            <DropdownTrigger>
              <Button isIconOnly size="sm" className="bg-transparent">
                <IconKebab isPassed />
              </Button>
            </DropdownTrigger>
            <DropdownMenu>
              <DropdownItem onClick={onClickReadAll}>모두 읽음 표시</DropdownItem>
              <DropdownItem onClick={onClickDeleteAll}>모두 삭제</DropdownItem>
            </DropdownMenu>
          </Dropdown>
        </div>
      </div>

      <section className="flex flex-col gap-[14px]">
        <h2 className="text-xl font-semibold">지난 한 주</h2>
        <div className="flex flex-col gap-3 md:gap-4">
          {notifications &&
            (listByDateStatus[0].length === 0 ? (
              <p className="text-sm md:text-base text-gray-2 dark:text-gray-3">지난 한 주 알림이 없습니다.</p>
            ) : (
              listByDateStatus[0].map((notification) => (
                <NotificationItem
                  key={notification.notification_id}
                  {...notification}
                  onClickRead={onClickRead}
                  onClickDelete={onClickDelete}
                />
              ))
            ))}
        </div>

        <Divider className="my-6" />

        <h2 className="text-xl font-semibold">지난 한 달</h2>
        <div className="flex flex-col gap-3 md:gap-4">
          {notifications &&
            (listByDateStatus[1].length === 0 ? (
              <p className="text-sm md:text-base text-gray-2 dark:text-gray-3">지난 한 달 알림이 없습니다.</p>
            ) : (
              listByDateStatus &&
              listByDateStatus[1].map((notification) => (
                <NotificationItem
                  key={notification.notification_id}
                  {...notification}
                  onClickRead={onClickRead}
                  onClickDelete={onClickDelete}
                />
              ))
            ))}
        </div>

        <Divider className="my-6" />

        <h2 className="text-xl font-semibold">지난 알림</h2>
        <div className="flex flex-col gap-3 md:gap-4">
          {notifications &&
            (listByDateStatus[2].length === 0 ? (
              <p className="text-sm md:text-base text-gray-2 dark:text-gray-3">지난 알림이 없습니다.</p>
            ) : (
              listByDateStatus &&
              listByDateStatus[2].map((notification) => (
                <NotificationItem
                  key={notification.notification_id}
                  {...notification}
                  onClickRead={onClickRead}
                  onClickDelete={onClickDelete}
                />
              ))
            ))}
        </div>
      </section>
    </section>
  );
}
