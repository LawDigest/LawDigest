'use client';

import { ElectionFeedItem, ScheduleFeedPayload } from '@/types';
import FeedTypeChip from './FeedTypeChip';

const EVENT_TYPE_CONFIG: Record<string, { label: string; className: string }> = {
  VOTER_ROLL: { label: '선거인명부', className: 'bg-gray-100 text-gray-500' },
  REGISTRATION: { label: '후보자 등록', className: 'bg-purple-50 text-purple-600' },
  CAMPAIGN: { label: '선거운동', className: 'bg-amber-50 text-amber-600' },
  EARLY_VOTING: { label: '사전투표', className: 'bg-blue-50 text-blue-600' },
  VOTING_DAY: { label: '선거일', className: 'bg-red-50 text-red-600' },
};

interface ScheduleCardProps {
  item: ElectionFeedItem;
}

export default function ScheduleCard({ item }: ScheduleCardProps) {
  const p = item.payload as ScheduleFeedPayload;
  const eventConfig = EVENT_TYPE_CONFIG[p.event_type] ?? {
    label: p.event_type,
    className: 'bg-gray-100 text-gray-500',
  };

  const dateStr = p.event_date
    ? new Date(`${p.event_date}T00:00:00`).toLocaleDateString('ko-KR', { month: 'long', day: 'numeric' })
    : '';

  return (
    <article className="bg-white dark:bg-dark-b p-4 rounded-xl border border-gray-200 dark:border-dark-l shadow-sm">
      <div className="flex items-center gap-2 mb-3">
        <FeedTypeChip type="schedule" />
        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${eventConfig.className}`}>
          {eventConfig.label}
        </span>
        <span className="ml-auto text-[10px] font-semibold text-gray-600 dark:text-gray-300 shrink-0">{dateStr}</span>
      </div>
      <p className="text-sm font-semibold text-gray-700 dark:text-white leading-snug mb-1">{p.title}</p>
      {p.description && <p className="text-[11px] text-gray-400 leading-relaxed line-clamp-2">{p.description}</p>}
    </article>
  );
}
