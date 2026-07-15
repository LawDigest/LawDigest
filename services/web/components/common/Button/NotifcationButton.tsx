'use client';

import Link from 'next/link';
import { IconNotification } from '@/public/svgs';
import { Badge } from '@heroui/badge';
import { useGetNotificationCount } from '@/app/notification/apis';
import { getCookie } from 'cookies-next';
import { ACCESS_TOKEN } from '@/constants';
import { useSetAtom } from 'jotai';
import { snackbarState } from '@/store';

export default function NotificationButton() {
  const accessToken = getCookie(ACCESS_TOKEN);
  const setSnackbar = useSetAtom(snackbarState);

  if (!accessToken) {
    return (
      <Link
        href="#"
        onClick={() =>
          setSnackbar({ show: true, type: 'ERROR', message: '로그인이 필요한 서비스입니다.', duration: 3000 })
        }>
        <IconNotification />
      </Link>
    );
  }
  // eslint-disable-next-line react-hooks/rules-of-hooks
  const { data: notificationCount } = useGetNotificationCount();

  if (notificationCount && notificationCount.notification_count === 0) {
    return (
      <Link href="/notification">
        <IconNotification />
      </Link>
    );
  }

  return (
    <Link href="/notification">
      <Badge shape="circle" content="" color="danger" size="sm">
        <IconNotification />
      </Badge>
    </Link>
  );
}
