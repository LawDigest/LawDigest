'use client';

import { ElectionFeedItem, PledgeFeedPayload } from '@/types';
import FeedTypeChip from './FeedTypeChip';
import { formatDate } from './utils';

interface PledgeCardProps {
  item: ElectionFeedItem;
}

export default function PledgeCard({ item }: PledgeCardProps) {
  const p = item.payload as PledgeFeedPayload;
  return (
    <article className="bg-white dark:bg-dark-b p-4 rounded-xl border border-gray-200 dark:border-dark-l shadow-sm">
      <div className="flex items-center gap-2 mb-3">
        <FeedTypeChip type="pledge" />
        {p.party_name && (
          <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-blue-50 text-blue-600">
            {p.party_name}
          </span>
        )}
        <span className="ml-auto text-[10px] text-gray-400 shrink-0">{formatDate(item.published_at)}</span>
      </div>
      <p className="text-sm font-semibold text-gray-700 dark:text-white leading-snug line-clamp-2 mb-2">
        {p.prms_title ?? '공약 제목 없음'}
      </p>
      {p.summary && <p className="text-[11px] text-gray-500 dark:text-gray-400 line-clamp-2 mb-2">{p.summary}</p>}
      <div className="flex items-center justify-between pt-3 border-t border-gray-100 dark:border-dark-l/30">
        <span className="text-[11px] text-gray-400 truncate">
          {[p.candidate_name, p.region].filter(Boolean).join(' · ')}
        </span>
      </div>
    </article>
  );
}
