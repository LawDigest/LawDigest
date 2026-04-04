// services/web/app/election/components/BillMiniCard.tsx
'use client';

import { Chip } from '@nextui-org/react';
import { BillMiniCardProps } from '../data/mockFeedData';

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' });
}

type BillMiniCardComponentProps = Omit<BillMiniCardProps, 'type' | 'id'>;

export default function BillMiniCard({
  briefSummary,
  billName,
  billStage,
  proposeDate,
}: BillMiniCardComponentProps) {
  return (
    <div className="rounded-2xl border border-gray-1 dark:border-dark-l bg-white dark:bg-dark-pb p-4 space-y-2">
      <div className="flex items-center gap-2">
        <span className="text-[10px] font-semibold rounded-full bg-default-100 dark:bg-dark-b px-2 py-0.5 text-gray-3 dark:text-gray-1">
          법안
        </span>
        <Chip size="sm" variant="bordered" className="text-[10px]">{billStage}</Chip>
        <span className="ml-auto text-[11px] text-gray-2">{formatDate(proposeDate)}</span>
      </div>
      <p className="text-sm font-semibold text-gray-4 dark:text-white leading-snug">{briefSummary}</p>
      <p className="text-[11px] text-gray-2 leading-snug">{billName}</p>
    </div>
  );
}
