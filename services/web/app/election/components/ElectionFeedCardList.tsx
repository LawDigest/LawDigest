'use client';

import { FeedItem, SnsFeedItem, PollFeedItem, BillMiniCardProps } from '../data/mockFeedData';
import BillMiniCard from './BillMiniCard';

const PLATFORM_LABEL: Record<string, string> = {
  twitter: 'X',
  facebook: 'Facebook',
  instagram: 'Instagram',
  youtube: 'YouTube',
};

function SnsCard({ item }: { item: SnsFeedItem }) {
  const timeLabel = new Date(item.publishedAt).toLocaleDateString('ko-KR', {
    month: 'short',
    day: 'numeric',
  });
  return (
    <div className="rounded-2xl border border-gray-1 dark:border-dark-l bg-white dark:bg-dark-pb p-4 space-y-2">
      <div className="flex items-center gap-2">
        <span className="text-[10px] font-semibold rounded-full bg-default-100 dark:bg-dark-b px-2 py-0.5 text-gray-3 dark:text-gray-1">
          SNS · {PLATFORM_LABEL[item.platform]}
        </span>
        <span className="text-xs text-gray-3 dark:text-gray-1 font-medium">{item.candidateName}</span>
        <span className="ml-auto text-[11px] text-gray-2">{timeLabel}</span>
      </div>
      <p className="text-sm text-gray-4 dark:text-white line-clamp-2">{item.content}</p>
      <a
        href={item.originalUrl}
        target="_blank"
        rel="noopener noreferrer"
        className="text-xs text-primary-2 hover:underline">
        원본 보기 →
      </a>
    </div>
  );
}

function PollCard({ item }: { item: PollFeedItem }) {
  const timeLabel = new Date(item.publishedAt).toLocaleDateString('ko-KR', {
    month: 'short',
    day: 'numeric',
  });
  return (
    <div className="rounded-2xl border border-gray-1 dark:border-dark-l bg-white dark:bg-dark-pb p-4 space-y-3">
      <div className="flex items-center gap-2">
        <span className="text-[10px] font-semibold rounded-full bg-default-100 dark:bg-dark-b px-2 py-0.5 text-gray-3 dark:text-gray-1">
          여론조사
        </span>
        <span className="text-xs text-gray-3 dark:text-gray-1">{item.pollster}</span>
        <span className="ml-auto text-[11px] text-gray-2">{timeLabel}</span>
      </div>
      <div className="space-y-2">
        {item.results.map((r) => (
          <div key={r.partyName} className="flex items-center gap-2">
            <span className="text-xs text-gray-3 dark:text-gray-1 w-[80px] shrink-0">{r.partyName}</span>
            <div className="flex-1 h-2 rounded-full bg-default-100 dark:bg-dark-b overflow-hidden">
              <div className="h-full rounded-full bg-primary-2" style={{ width: `${r.pct}%` }} />
            </div>
            <span className="text-xs font-semibold text-gray-4 dark:text-white w-9 text-right">{r.pct}%</span>
            <span
              className={`text-[10px] w-12 text-right ${
                r.delta > 0 ? 'text-red-500' : r.delta < 0 ? 'text-blue-500' : 'text-gray-2'
              }`}>
              {r.delta > 0 ? `▲${r.delta}` : r.delta < 0 ? `▼${Math.abs(r.delta)}` : '-'}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

interface ElectionFeedCardListProps {
  items: FeedItem[];
}

export default function ElectionFeedCardList({ items }: ElectionFeedCardListProps) {
  if (items.length === 0) {
    return <p className="text-center py-12 text-sm text-gray-2">아직 등록된 선거 피드가 없습니다.</p>;
  }
  return (
    <div className="space-y-3 px-4 pb-6">
      {items.map((item) => {
        if (item.type === 'sns') return <SnsCard key={item.id} item={item as SnsFeedItem} />;
        if (item.type === 'poll') return <PollCard key={item.id} item={item as PollFeedItem} />;
        if (item.type === 'bill') {
          const b = item as BillMiniCardProps;
          return (
            <BillMiniCard
              key={b.id}
              briefSummary={b.briefSummary}
              billName={b.billName}
              billStage={b.billStage}
              proposeDate={b.proposeDate}
              partyName={b.partyName}
            />
          );
        }
        return null;
      })}
    </div>
  );
}
