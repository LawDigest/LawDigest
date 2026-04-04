'use client';

import { MOCK_FEED_ITEMS, FeedItem, SnsFeedItem, PollFeedItem } from '../data/mockFeedData';
import ElectionFeedCardList from './ElectionFeedCardList';

interface FeedRegionPanelProps {
  region: string;
}

export default function FeedRegionPanel({ region }: FeedRegionPanelProps) {
  // bill 타입은 region 필드가 없으므로 제외하고, sns/poll만 지역 필터링
  const filtered: FeedItem[] = MOCK_FEED_ITEMS.filter((item) => {
    if (item.type === 'bill') return false;
    return (item as SnsFeedItem | PollFeedItem).region === region;
  });

  // 해당 지역 데이터가 없으면 sns/poll 항목 중 최신 3개를 보여줌 (폴백)
  const items: FeedItem[] =
    filtered.length > 0 ? filtered : MOCK_FEED_ITEMS.filter((i) => i.type !== 'bill').slice(0, 3);

  return (
    <div className="space-y-3">
      <h3 className="px-4 text-sm font-semibold text-gray-4 dark:text-white">{region} 관련 피드</h3>
      <ElectionFeedCardList items={items} />
    </div>
  );
}
