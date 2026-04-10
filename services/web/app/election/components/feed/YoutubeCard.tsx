'use client';

import Image from 'next/image';
import { YoutubeFeedItem } from '../../data/mockFeedData';
import FeedTypeChip from './FeedTypeChip';
import { timeAgo, formatCount } from './utils';

interface YoutubeCardProps {
  item: YoutubeFeedItem;
}

export default function YoutubeCard({ item }: YoutubeCardProps) {
  return (
    <article className="bg-white dark:bg-dark-b p-4 rounded-xl border border-gray-200 dark:border-dark-l shadow-sm">
      {/* 헤더 */}
      <div className="flex items-center gap-2 mb-3">
        <FeedTypeChip type="youtube" />
        <span className="text-xs text-gray-400 truncate flex-1">
          {item.candidateName} · {item.partyName}
        </span>
        <span className="text-[10px] text-gray-400 shrink-0">{timeAgo(item.publishedAt)}</span>
      </div>
      {/* 수평 레이아웃: 썸네일 좌측 고정 + 우측 텍스트 */}
      <div className="flex gap-3">
        <div className="relative w-[140px] shrink-0 rounded-lg overflow-hidden" style={{ aspectRatio: '16/9' }}>
          <Image src={item.thumbnailUrl} alt={item.title} fill unoptimized className="object-cover" />
          <div className="absolute inset-0 bg-black/25 flex items-center justify-center">
            <button
              type="button"
              aria-label="영상 재생"
              className="w-10 h-10 bg-white/20 backdrop-blur-sm rounded-full flex items-center justify-center border border-white/30">
              <span className="material-symbols-outlined text-white text-2xl" aria-hidden="true">
                play_arrow
              </span>
            </button>
          </div>
        </div>
        {/* 우측 텍스트 */}
        <div className="flex-1 min-w-0 flex flex-col justify-between">
          <h2 className="text-sm font-bold text-gray-700 dark:text-white leading-snug line-clamp-3">{item.title}</h2>
          <div className="flex items-center gap-3 mt-2 text-gray-400">
            <span className="text-[10px] truncate">{item.channelName}</span>
            <div className="ml-auto flex items-center gap-2.5 shrink-0">
              <span className="flex items-center gap-0.5">
                <span className="material-symbols-outlined text-[14px]" aria-hidden="true">
                  thumb_up
                </span>
                <span className="text-[10px] font-medium">{formatCount(item.likes)}</span>
              </span>
            </div>
          </div>
        </div>
      </div>
    </article>
  );
}
