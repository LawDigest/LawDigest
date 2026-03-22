'use client';

import { useCallback, useState } from 'react';
import { Button } from '@nextui-org/react';
import { getCookie } from 'cookies-next';
import { ACCESS_TOKEN } from '@/constants';
import { useSetRecoilState } from 'recoil';
import { snackbarState } from '@/store';
import { IconCheck, IconPlus } from '@/public/svgs';
import { usePatchPartyFollow } from '../../apis';

export default function FollowBoard({
  id,
  followed,
  follow_count,
  representative_bill_count,
  public_bill_count,
}: {
  id: number;
  followed: boolean;
  follow_count: number;
  representative_bill_count: number;
  public_bill_count: number;
}) {
  const [isFollowed, setIsFollowed] = useState(followed);
  const [followCount, setFollowCount] = useState(follow_count);
  const mutationFollow = usePatchPartyFollow(id);
  const setSnackbar = useSetRecoilState(snackbarState);

  const onClickFollow = useCallback(() => {
    const accessToken = getCookie(ACCESS_TOKEN);

    if (accessToken) {
      setIsFollowed(!isFollowed);
      setFollowCount(isFollowed ? followCount - 1 : followCount + 1);
      setSnackbar({
        show: true,
        type: isFollowed ? 'CANCEL' : 'SUCCESS',
        message: isFollowed ? '해당 정당의 팔로우를 취소했습니다.' : '해당 정당을 팔로우했습니다.',
        duration: 3000,
      });

      mutationFollow.mutate(!isFollowed);
    } else {
      setSnackbar({ show: true, type: 'ERROR', message: '로그인이 필요한 서비스입니다.', duration: 3000 });
    }
  }, [isFollowed, followed, setSnackbar]);

  return (
    <section className="flex flex-col gap-5">
      <div className="grid grid-cols-3 gap-10">
        <div className="flex flex-col items-center gap-[10px]">
          <p className="text-2xl font-semibold">{followCount}</p>
          <p className="text-sm font-medium text-gray-2 dark:text-gray-3">팔로워</p>
        </div>
        <div className="flex flex-col items-center gap-[10px]">
          <p className="text-2xl font-semibold"> {representative_bill_count}</p>
          <p className="text-sm font-medium text-gray-2 dark:text-gray-3">대표발의법안</p>
        </div>
        <div className="flex flex-col items-center gap-[10px]">
          <p className="text-2xl font-semibold"> {public_bill_count}</p>
          <p className="text-sm font-medium text-gray-2 dark:text-gray-3">공동발의법안</p>
        </div>
      </div>

      <Button
        radius="full"
        onClick={onClickFollow}
        endContent={isFollowed ? <IconCheck /> : <IconPlus />}
        className={`w-full h-12 text-lg font-medium flex justify-between px-6 ${isFollowed ? 'bg-gray-1 text-gray-3' : 'bg-primary-3 text-white dark:bg-gray-4 dark:text-gray-2'} `}>
        {isFollowed ? '팔로우 취소' : '팔로우'}
      </Button>
    </section>
  );
}
