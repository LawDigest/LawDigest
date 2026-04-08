'use client';

import { type SnsPlatform } from '../../data/mockFeedData';

type FeedType = 'poll' | 'sns' | 'bill' | 'youtube' | 'image';

interface FeedTypeChipProps {
  type: FeedType;
  platform?: SnsPlatform;
}

const CHIP_CONFIG: Record<FeedType, { label: string; icon: string; className: string }> = {
  poll:    { label: '여론조사', icon: 'bar_chart',  className: 'bg-red-50 text-red-600' },
  sns:     { label: 'SNS',    icon: 'tag',         className: 'bg-blue-50 text-blue-600' },
  bill:    { label: '법안',   icon: 'gavel',       className: 'bg-green-50 text-green-700' },
  youtube: { label: '영상',   icon: 'play_circle', className: 'bg-purple-50 text-purple-600' },
  image:   { label: '이미지', icon: 'image',       className: 'bg-gray-50 text-gray-500' },
};

const PLATFORM_ICON: Record<SnsPlatform, string> = {
  twitter:   'tag',
  facebook:  'public',
  instagram: 'photo_camera',
  youtube:   'play_circle',
};

export default function FeedTypeChip({ type, platform }: FeedTypeChipProps) {
  const config = CHIP_CONFIG[type];
  const icon = type === 'sns' && platform ? PLATFORM_ICON[platform] : config.icon;
  return (
    <span className={`inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full ${config.className}`}>
      <span className="material-symbols-outlined text-[11px]" style={{ fontVariationSettings: "'FILL' 1" }}>
        {icon}
      </span>
      {config.label}
    </span>
  );
}
