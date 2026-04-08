'use client';

import { PollFeedItem } from '../../data/mockFeedData';
import FeedTypeChip from './FeedTypeChip';
import { timeAgo } from './utils';

function DeltaBadge({ delta }: { delta: number }) {
  if (delta > 0) return <span className="text-[10px] w-10 text-right font-medium text-blue-500">▲{delta}</span>;
  if (delta < 0)
    return <span className="text-[10px] w-10 text-right font-medium text-red-400">▼{Math.abs(delta)}</span>;
  return <span className="text-[10px] w-10 text-right font-medium text-gray-400">-</span>;
}

interface PollCardProps {
  item: PollFeedItem;
}

export default function PollCard({ item }: PollCardProps) {
  const maxPct = Math.max(...item.results.map((r) => r.pct));
  return (
    <article className="bg-white dark:bg-dark-b p-4 rounded-xl border border-gray-200 dark:border-dark-l shadow-sm">
      <div className="flex items-center gap-2 mb-3">
        <FeedTypeChip type="poll" />
        <span className="text-xs font-semibold text-gray-700 dark:text-white truncate">{item.pollster}</span>
        <span className="text-[10px] text-gray-400 shrink-0">{item.region}</span>
        <span className="ml-auto text-[10px] text-gray-400 shrink-0">{timeAgo(item.publishedAt)}</span>
      </div>
      <div className="space-y-2.5">
        {item.results.map((r) => (
          <div key={r.partyName} className="flex items-center gap-2">
            <span className="text-xs text-gray-600 dark:text-gray-300 w-[80px] shrink-0 truncate">{r.partyName}</span>
            <div className="flex-1 h-3 rounded-full bg-gray-100 dark:bg-dark-l overflow-hidden">
              <div
                className="h-full rounded-full"
                style={{ width: `${(r.pct / maxPct) * 100}%`, backgroundColor: r.color }}
              />
            </div>
            <span className="text-xs font-bold text-gray-700 dark:text-white w-10 text-right tabular-nums">
              {r.pct}%
            </span>
            <DeltaBadge delta={r.delta} />
          </div>
        ))}
      </div>
    </article>
  );
}
