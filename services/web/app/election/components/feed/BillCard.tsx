'use client';

import { BillFeedItem } from '../../data/mockFeedData';
import FeedTypeChip from './FeedTypeChip';
import { formatDate } from './utils';

interface BillCardProps {
  item: BillFeedItem;
}

const STAGE_CONFIG: Record<string, { className: string }> = {
  접수: { className: 'bg-gray-100 text-gray-500' },
  '위원회 심사': { className: 'bg-blue-50 text-blue-600' },
  '본회의 심의': { className: 'bg-amber-50 text-amber-600' },
  통과: { className: 'bg-green-100 text-green-700' },
};

export default function BillCard({ item }: BillCardProps) {
  const stageClass = STAGE_CONFIG[item.billStage]?.className ?? 'bg-gray-100 text-gray-500';
  return (
    <article className="bg-white dark:bg-dark-b p-4 rounded-xl border border-gray-200 dark:border-dark-l shadow-sm">
      <div className="flex items-center gap-2 mb-3">
        <FeedTypeChip type="bill" />
        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${stageClass}`}>{item.billStage}</span>
        <span className="ml-auto text-[10px] text-gray-400 shrink-0">{formatDate(item.proposeDate)}</span>
      </div>
      <p className="text-sm font-semibold text-gray-700 dark:text-white leading-snug line-clamp-2 mb-2">
        {item.briefSummary}
      </p>
      <div className="flex items-center justify-between pt-3 border-t border-gray-100 dark:border-dark-l/30">
        <span className="text-[11px] text-gray-400 truncate">{item.billName}</span>
        <button type="button" className="shrink-0 ml-3 text-[11px] font-bold text-blue-500 hover:underline">
          자세히
        </button>
      </div>
    </article>
  );
}
