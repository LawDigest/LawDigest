'use client';

import Link from 'next/link';
import { IconNotification } from '@/public/svgs';
import { Badge } from '@nextui-org/badge';
import { useGetNotificationCount } from '@/app/notification/apis';
import { getCookie } from 'cookies-next';
import { ACCESS_TOKEN } from '@/constants';
import { useSetRecoilState } from 'recoil';
import { snackbarState } from '@/store';

export default function NotificationButton() {
  const accessToken = getCookie(ACCESS_TOKEN);
  const setSnackbar = useSetRecoilState(snackbarState);

  if (!accessToken) {
    return (
      // eslint-disable-next-line jsx-a11y/anchor-is-valid
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
