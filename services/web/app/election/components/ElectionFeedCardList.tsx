'use client';

import { FeedItem, SnsFeedItem, PollFeedItem, BillMiniCardProps, YoutubeFeedItem, ImageFeedItem } from '../data/mockFeedData';
import { SnsCard, YoutubeCard, PollCard, BillCard, ImageCard } from './feed';

interface ElectionFeedCardListProps {
  items: FeedItem[];
  emptyMessage?: string;
}

export default function ElectionFeedCardList({ items, emptyMessage }: ElectionFeedCardListProps) {
  if (items.length === 0) {
    return (
      <p className="text-center py-12 text-sm text-gray-400">
        {emptyMessage ?? '아직 등록된 선거 피드가 없습니다.'}
      </p>
    );
  }
  return (
    <div className="space-y-3 px-4 pb-6">
      {items.map((item) => {
        if (item.type === 'youtube') return <YoutubeCard key={item.id} item={item as YoutubeFeedItem} />;
        if (item.type === 'sns')     return <SnsCard     key={item.id} item={item as SnsFeedItem} />;
        if (item.type === 'bill')    return <BillCard    key={item.id} item={item as BillMiniCardProps} />;
        if (item.type === 'poll')    return <PollCard    key={item.id} item={item as PollFeedItem} />;
        if (item.type === 'image')   return <ImageCard   key={item.id} item={item as ImageFeedItem} />;
        return null;
      })}
    </div>
  );
}
