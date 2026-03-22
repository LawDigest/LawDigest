'use client';

import React, { useCallback } from 'react';
import { Button, Divider } from '@nextui-org/react';
import { getCookie } from 'cookies-next';
import { useSetRecoilState } from 'recoil';
import { ACCESS_TOKEN } from '@/constants';
import { snackbarState } from '@/store';
import {
  useGetNotificationTopThree,
  usePutNotificationRead,
  useDeleteNotification,
  useGetNotificationCount,
} from '../apis';
import NotificationItem from './NotificationItem';

export default function NotificationTopThree() {
  const accessToken = getCookie(ACCESS_TOKEN);
  const { data: notifications, isLoading } = useGetNotificationTopThree({
    enabled: Boolean(accessToken),
  });
  const { data: notificationCount } = useGetNotificationCount({
    enabled: Boolean(accessToken),
  });
  const setSnackbar = useSetRecoilState(snackbarState);

  const mutateRead = usePutNotificationRead({
    onSuccess: () => {
      setSnackbar({
        show: true,
        type: 'SUCCESS',
        message: '해당 알림을 읽었습니다.',
        duration: 3000,
      });
    },
    onError: () => {
      setSnackbar({
        show: true,
        type: 'ERROR',
        message: '알림 읽기에 실패했습니다.',
        duration: 3000,
      });
    },
  });

  const mutateDelete = useDeleteNotification({
    onSuccess: () => {
      setSnackbar({
        show: true,
        type: 'CANCEL',
        message: '해당 알림을 삭제했습니다.',
        duration: 3000,
      });
    },
    onError: () => {
      setSnackbar({
        show: true,
        type: 'ERROR',
        message: '알림 삭제에 실패했습니다.',
        duration: 3000,
      });
    },
  });

  const handleRead = useCallback(
    (notificationId: number) => {
      mutateRead.mutate(notificationId);
    },
    [mutateRead],
  );

  const handleDelete = useCallback(
    (notificationId: number) => {
      mutateDelete.mutate(notificationId);
    },
    [mutateDelete],
  );

  if (!accessToken) return null;
  if (isLoading) return <p className="text-sm text-center text-gray-2 dark:text-gray-3">불러오는 중...</p>;

  return (
    <section className="mx-4 mt-6 mb-10 flex flex-col gap-4 rounded-xl border border-gray-1 p-5 dark:border-dark-l md:mx-6">
      <h2 className="text-xl font-semibold">최근 알림</h2>
      <Divider />

      {notifications && notifications.length > 0 ? (
        <div className="flex flex-col gap-3 md:gap-4">
          {notifications.map((notification) => (
            <NotificationItem
              key={notification.notification_id}
              {...notification}
              onClickRead={handleRead}
              onClickDelete={handleDelete}
            />
          ))}
        </div>
      ) : (
        <p className="text-sm md:text-base text-gray-2 dark:text-gray-3">최근 알림이 없습니다.</p>
      )}

      {/* 푸터: 왼쪽 읽지 않은 알림 수, 오른쪽 더보기 버튼 */}
      <div className="flex justify-between items-center mt-4">
        {notificationCount && (
          <p className="text-xs md:text-sm text-gray-2 dark:text-gray-3">
            <span className="text-black dark:text-gray-2">{notificationCount.notification_count}개</span>의 읽지 않은
            알림이 있습니다.
          </p>
        )}
        <Button as="a" href="/notification" variant="light" size="sm" className="text-xs md:text-sm">
          알림 더 보기
        </Button>
      </div>
    </section>
  );
}
