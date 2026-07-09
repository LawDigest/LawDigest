'use client';

import clsx from 'clsx';

/** 통계 카드 로딩 상태에 쓰는 공용 펄스 블록. */
export function SkeletonBar({ className }: { className?: string }) {
  return <div className={clsx('animate-pulse rounded-md bg-gray-0.5 dark:bg-dark-l', className)} />;
}
