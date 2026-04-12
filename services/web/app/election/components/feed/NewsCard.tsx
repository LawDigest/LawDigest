'use client';

import { ElectionFeedItem, NewsFeedPayload } from '@/types';
import FeedTypeChip from './FeedTypeChip';
import { formatDate } from './utils';

interface NewsCardProps {
  item: ElectionFeedItem;
}

export default function NewsCard({ item }: NewsCardProps) {
  const p = item.payload as NewsFeedPayload;
  return (
    <a
      href={p.link}
      target="_blank"
      rel="noopener noreferrer"
      className="block bg-white dark:bg-dark-b p-4 rounded-xl border border-gray-200 dark:border-dark-l shadow-sm hover:shadow-md transition-shadow">
      <div className="flex gap-3">
        {/* 텍스트 영역 */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-2">
            <FeedTypeChip type="news" />
            {p.matched_party && (
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-blue-50 text-blue-600">
                {p.matched_party}
              </span>
            )}
            <span className="ml-auto text-[10px] text-gray-400 shrink-0">{formatDate(item.published_at)}</span>
          </div>
          <p className="text-sm font-semibold text-gray-700 dark:text-white leading-snug line-clamp-2 mb-1">
            {p.title}
          </p>
          {p.description && (
            <p className="text-[11px] text-gray-500 dark:text-gray-400 line-clamp-2 mb-2">{p.description}</p>
          )}
          <span className="text-[10px] text-gray-400">{[p.source, p.matched_region].filter(Boolean).join(' · ')}</span>
        </div>

        {/* 썸네일 */}
        {p.thumbnail_url && (
          <div className="w-20 h-20 shrink-0 rounded-lg overflow-hidden bg-gray-100">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={p.thumbnail_url} alt="" className="w-full h-full object-cover" />
          </div>
        )}
      </div>
    </a>
  );
}
