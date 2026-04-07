'use client';

import Image from 'next/image';
import {
  FeedItem,
  SnsFeedItem,
  PollFeedItem,
  BillMiniCardProps,
  YoutubeFeedItem,
  ImageFeedItem,
} from '../data/mockFeedData';

const PLATFORM_ICON: Record<string, string> = {
  twitter: 'tag',
  facebook: 'public',
  instagram: 'photo_camera',
  youtube: 'play_circle',
};

function timeAgo(dateStr: string): string {
  const diff = Math.floor((Date.now() - new Date(dateStr).getTime()) / 1000);
  if (diff < 3600) return `${Math.floor(diff / 60)}분 전`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}시간 전`;
  return `${Math.floor(diff / 86400)}일 전`;
}

function formatCount(n?: number): string {
  if (!n) return '0';
  if (n >= 1000) return `${(n / 1000).toFixed(1)}k`;
  return String(n);
}

function DeltaBadge({ delta }: { delta: number }) {
  if (delta > 0) return <span className="text-[10px] w-10 text-right font-medium text-gray-3">▲{delta}</span>;
  if (delta < 0) return <span className="text-[10px] w-10 text-right font-medium text-gray-2">▼{Math.abs(delta)}</span>;
  return <span className="text-[10px] w-10 text-right font-medium text-gray-2">-</span>;
}

/** YouTube 카드 — 썸네일 + 재생 버튼 */
function YoutubeCard({ item }: { item: YoutubeFeedItem }) {
  return (
    <article className="bg-white dark:bg-dark-b rounded-xl overflow-hidden border border-gray-1 shadow-sm group">
      <div className="relative aspect-video overflow-hidden">
        <Image
          src={item.thumbnailUrl}
          alt={item.title}
          fill
          unoptimized
          className="object-cover group-hover:scale-105 transition-transform duration-500"
        />
        <div className="absolute inset-0 bg-black/20 flex items-center justify-center">
          <div className="w-16 h-16 bg-white/20 backdrop-blur-md rounded-full flex items-center justify-center border border-white/30">
            <span
              className="material-symbols-outlined text-white text-4xl"
              style={{ fontVariationSettings: "'FILL' 1" }}>
              play_arrow
            </span>
          </div>
        </div>
      </div>
      <div className="p-5">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-8 h-8 rounded-full bg-primary-1 flex items-center justify-center">
            <span className="material-symbols-outlined text-primary-2 text-sm">person</span>
          </div>
          <div>
            <p className="text-xs font-bold text-gray-4 dark:text-white leading-tight">{item.candidateName}</p>
            <p className="text-[10px] text-gray-2">
              {item.channelName} · {timeAgo(item.publishedAt)}
            </p>
          </div>
        </div>
        <h2 className="text-lg font-bold text-gray-4 dark:text-white mb-2 leading-tight">{item.title}</h2>
        <div className="flex items-center gap-4 mt-4">
          <button
            type="button"
            className="flex items-center gap-1.5 text-gray-2 hover:text-primary-2 transition-colors">
            <span className="material-symbols-outlined text-xl">thumb_up</span>
            <span className="text-xs font-medium">{formatCount(item.likes)}</span>
          </button>
          <button
            type="button"
            className="flex items-center gap-1.5 text-gray-2 hover:text-primary-2 transition-colors">
            <span className="material-symbols-outlined text-xl">chat_bubble</span>
            <span className="text-xs font-medium">{formatCount(item.comments)}</span>
          </button>
          <button
            type="button"
            className="ml-auto flex items-center gap-1.5 text-gray-2 hover:text-primary-2 transition-colors">
            <span className="material-symbols-outlined text-xl">share</span>
          </button>
        </div>
      </div>
    </article>
  );
}

/** SNS 포스트 카드 — X/인스타 스타일 */
function SnsCard({ item }: { item: SnsFeedItem }) {
  return (
    <article className="bg-white dark:bg-dark-b p-5 rounded-xl border border-gray-1 shadow-sm">
      <div className="flex gap-4">
        <div className="flex-shrink-0">
          <div className="w-12 h-12 rounded-full bg-primary-1 flex items-center justify-center">
            <span className="material-symbols-outlined text-primary-2">person</span>
          </div>
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2">
            <div className="min-w-0">
              <span className="text-sm font-bold text-gray-4 dark:text-white">{item.candidateName}</span>
              <span className="text-xs text-gray-2 ml-1">{item.partyName}</span>
            </div>
            <div className="flex items-center gap-1 shrink-0">
              <span className="material-symbols-outlined text-gray-2 text-sm">
                {PLATFORM_ICON[item.platform] ?? 'public'}
              </span>
              <span className="text-[10px] text-gray-2">{timeAgo(item.publishedAt)}</span>
            </div>
          </div>
          <p className="text-sm text-gray-4 dark:text-white mt-2 leading-relaxed">{item.content}</p>
          {item.quoteText && (
            <div className="mt-3 p-3 bg-gray-0.5 dark:bg-dark-l/30 rounded-lg border-l-4 border-primary-2/40">
              <p className="text-xs text-gray-2 italic">{item.quoteText}</p>
            </div>
          )}
          <div className="flex items-center gap-6 mt-4 text-gray-2">
            <div className="flex items-center gap-1.5 hover:text-primary-2 cursor-pointer transition-colors">
              <span className="material-symbols-outlined text-lg">mode_comment</span>
              <span className="text-[11px] font-bold">{formatCount(item.comments)}</span>
            </div>
            <div className="flex items-center gap-1.5 hover:text-gray-3 cursor-pointer transition-colors">
              <span className="material-symbols-outlined text-lg">recycling</span>
              <span className="text-[11px] font-bold">{formatCount(item.retweets)}</span>
            </div>
            <div className="flex items-center gap-1.5 hover:text-error cursor-pointer transition-colors">
              <span className="material-symbols-outlined text-lg">favorite</span>
              <span className="text-[11px] font-bold">{formatCount(item.likes)}</span>
            </div>
          </div>
        </div>
      </div>
    </article>
  );
}

/** 법안/공식 발표 카드 */
function BillCard({ item }: { item: BillMiniCardProps }) {
  const STAGE_COLOR: Record<string, string> = {
    접수: 'bg-gray-0.5 dark:bg-dark-l text-gray-2',
    '위원회 심사': 'bg-primary-1 text-primary-2',
    '본회의 심의': 'bg-gray-3/10 text-gray-3',
    통과: 'bg-green-100 text-green-700',
  };
  const stageClass = STAGE_COLOR[item.billStage] ?? 'bg-gray-0.5 dark:bg-dark-l text-gray-2';

  return (
    <article className="bg-gray-0.5 dark:bg-dark-l/30 p-5 rounded-xl relative overflow-hidden border border-gray-1 shadow-sm">
      <div className="absolute top-0 right-0 p-4 opacity-10">
        <span className="material-symbols-outlined text-6xl text-gray-3">gavel</span>
      </div>
      <div className="flex items-center gap-2 mb-3">
        <span className="bg-gray-3/10 text-gray-3 text-[10px] font-extrabold px-2 py-0.5 rounded-full tracking-wider uppercase">
          법안 · {item.partyName}
        </span>
        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${stageClass}`}>{item.billStage}</span>
      </div>
      <h2 className="text-base font-extrabold text-gray-4 dark:text-white mb-2 leading-snug pr-8">
        {item.briefSummary}
      </h2>
      <div className="flex items-center justify-between border-t border-gray-1/50 pt-3 mt-3">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded bg-gray-4 flex items-center justify-center">
            <span className="material-symbols-outlined text-white text-[14px]">account_balance</span>
          </div>
          <span className="text-xs font-bold text-gray-4 dark:text-white">{item.billName}</span>
        </div>
        <button type="button" className="bg-primary-2 text-white px-3 py-1.5 rounded-full text-xs font-bold shadow-sm">
          자세히
        </button>
      </div>
    </article>
  );
}

/** 여론조사 카드 */
function PollCard({ item }: { item: PollFeedItem }) {
  return (
    <article className="bg-gray-0.5 dark:bg-dark-l/30 p-5 rounded-xl relative overflow-hidden border border-gray-1 shadow-sm">
      <div className="absolute top-0 right-0 p-4 opacity-10">
        <span className="material-symbols-outlined text-6xl text-primary-2">poll</span>
      </div>
      <div className="flex items-center gap-2 mb-3">
        <span className="bg-primary-1 text-primary-2 text-[10px] font-extrabold px-2 py-0.5 rounded-full tracking-wider uppercase">
          여론조사
        </span>
        <span className="text-[10px] text-gray-2">{timeAgo(item.publishedAt)}</span>
      </div>
      <h2 className="text-base font-extrabold text-gray-4 dark:text-white mb-3 leading-snug">
        {item.pollster} · {item.region}
      </h2>
      <div className="space-y-2.5 pr-8">
        {item.results.map((r) => (
          <div key={r.partyName} className="flex items-center gap-2">
            <span className="text-xs text-gray-2 w-[88px] shrink-0">{r.partyName}</span>
            <div className="flex-1 h-2 rounded-full bg-gray-0.5 dark:bg-dark-l overflow-hidden">
              <div className="h-full rounded-full bg-primary-2" style={{ width: `${r.pct}%` }} />
            </div>
            <span className="text-xs font-semibold text-gray-4 dark:text-white w-9 text-right">{r.pct}%</span>
            <DeltaBadge delta={r.delta} />
          </div>
        ))}
      </div>
    </article>
  );
}

/** 이미지 업데이트 카드 */
function ImageCard({ item }: { item: ImageFeedItem }) {
  return (
    <article className="bg-white dark:bg-dark-b rounded-xl overflow-hidden border border-gray-1 shadow-sm">
      <div className="p-5 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-full bg-primary-2 text-white flex items-center justify-center font-bold text-xs">
            {item.groupName.charAt(0)}
          </div>
          <div>
            <p className="text-xs font-bold text-gray-4 dark:text-white leading-tight">{item.groupName}</p>
            <p className="text-[10px] text-gray-2">{timeAgo(item.publishedAt)}</p>
          </div>
        </div>
        <button type="button" className="material-symbols-outlined text-gray-2">
          more_horiz
        </button>
      </div>
      {item.images.length > 0 && (
        <div className={`grid gap-1 px-1 ${item.images.length >= 2 ? 'grid-cols-2' : 'grid-cols-1'}`}>
          {item.images.slice(0, 2).map((img) => (
            <div key={img.src} className="relative aspect-square w-full">
              <Image src={img.src} alt={img.alt} fill unoptimized className="object-cover" />
            </div>
          ))}
        </div>
      )}
      <div className="p-5">
        <p className="text-sm text-gray-4 dark:text-white leading-relaxed">{item.content}</p>
      </div>
    </article>
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
    <div className="space-y-4 px-4 pb-6">
      {items.map((item) => {
        if (item.type === 'youtube') return <YoutubeCard key={item.id} item={item as YoutubeFeedItem} />;
        if (item.type === 'sns') return <SnsCard key={item.id} item={item as SnsFeedItem} />;
        if (item.type === 'bill') return <BillCard key={item.id} item={item as BillMiniCardProps} />;
        if (item.type === 'poll') return <PollCard key={item.id} item={item as PollFeedItem} />;
        if (item.type === 'image') return <ImageCard key={item.id} item={item as ImageFeedItem} />;
        return null;
      })}
    </div>
  );
}
