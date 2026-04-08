'use client';

import { SnsFeedItem } from '../../data/mockFeedData';
import FeedTypeChip from './FeedTypeChip';
import { timeAgo, formatCount } from './utils';

interface SnsCardProps {
  item: SnsFeedItem;
}

export default function SnsCard({ item }: SnsCardProps) {
  return (
    <article className="bg-white dark:bg-dark-b p-4 rounded-xl border border-gray-200 dark:border-dark-l shadow-sm">
      {/* 헤더 */}
      <div className="flex items-center gap-2 mb-3">
        <FeedTypeChip type="sns" platform={item.platform} />
        <div className="flex items-center gap-1 min-w-0 flex-1">
          <span className="text-xs font-bold text-gray-700 dark:text-white truncate">{item.candidateName}</span>
          <span className="text-[10px] text-gray-400 shrink-0">·</span>
          <span className="text-[10px] text-gray-400 shrink-0">{item.partyName}</span>
        </div>
        <span className="text-[10px] text-gray-400 shrink-0">{timeAgo(item.publishedAt)}</span>
      </div>
      {/* 본문 */}
      <p className="text-sm text-gray-700 dark:text-white leading-relaxed line-clamp-3">{item.content}</p>
      {/* 액션 */}
      <div className="flex items-center gap-5 mt-3 pt-3 border-t border-gray-100 dark:border-dark-l/30 text-gray-400">
        <span className="flex items-center gap-1">
          <span className="material-symbols-outlined text-[16px]">mode_comment</span>
          <span className="text-[11px] font-medium">{formatCount(item.comments)}</span>
        </span>
        <span className="flex items-center gap-1">
          <span className="material-symbols-outlined text-[16px]">recycling</span>
          <span className="text-[11px] font-medium">{formatCount(item.retweets)}</span>
        </span>
        <span className="flex items-center gap-1">
          <span className="material-symbols-outlined text-[16px]">favorite</span>
          <span className="text-[11px] font-medium">{formatCount(item.likes)}</span>
        </span>
      </div>
    </article>
  );
}
