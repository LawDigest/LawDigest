'use client';

import Image from 'next/image';
import { ImageFeedItem } from '../../data/mockFeedData';
import FeedTypeChip from './FeedTypeChip';
import { timeAgo } from './utils';

interface ImageCardProps {
  item: ImageFeedItem;
}

export default function ImageCard({ item }: ImageCardProps) {
  return (
    <article className="bg-white dark:bg-dark-b rounded-xl border border-gray-200 dark:border-dark-l shadow-sm overflow-hidden">
      <div className="p-4">
        <div className="flex items-center gap-2 mb-3">
          <FeedTypeChip type="image" />
          <span className="text-xs font-bold text-gray-700 dark:text-white truncate flex-1">{item.groupName}</span>
          <span className="text-[10px] text-gray-400 shrink-0">{timeAgo(item.publishedAt)}</span>
        </div>
        <p className="text-sm text-gray-700 dark:text-white leading-relaxed line-clamp-3">{item.content}</p>
      </div>
      {item.images.length > 0 && (
        <div className={`grid gap-0.5 ${item.images.length >= 2 ? 'grid-cols-2' : 'grid-cols-1'}`}>
          {item.images.slice(0, 4).map((img) => (
            <div key={img.src} className="relative aspect-square w-full">
              <Image src={img.src} alt={img.alt} fill unoptimized className="object-cover" />
            </div>
          ))}
        </div>
      )}
    </article>
  );
}
