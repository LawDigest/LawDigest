'use client';

import { Bar, BarChart, Cell, LabelList, XAxis, YAxis } from 'recharts';
import { ChartConfig, ChartContainer, ChartTooltip, ChartTooltipContent } from '@/components/ui/chart';
import { StatisticsStage, useGetStatisticsStage } from '../apis';
import StatsCard from './StatsCard';
import { SkeletonBar } from './StatsSkeleton';

// Neutral First: soft assembly blue 단색의 불투명도 램프(뒤 단계일수록 진하게).
const STAGES: { key: keyof StatisticsStage; label: string; opacity: number }[] = [
  { key: 'receipt_count', label: '접수', opacity: 0.4 },
  { key: 'committee_count', label: '위원회 심사', opacity: 0.6 },
  { key: 'plenary_count', label: '본회의 심의', opacity: 0.8 },
  { key: 'promulgated_count', label: '공포', opacity: 1 },
];

const STAGE_BLUE = '#96BCFA';

const chartConfig = {
  count: { label: '도달 건수' },
} satisfies ChartConfig;

/** 입법 진행 단계 퍼널 — 접수 대비 누적 도달 비율(가로 막대). */
export default function StatsStageFunnel() {
  const { data, isLoading } = useGetStatisticsStage();
  const stage = data?.data;

  if (isLoading) {
    return (
      <StatsCard title="입법 진행 단계" icon="filter_alt" delay={0.05}>
        <div className="flex h-[190px] flex-col justify-between py-1">
          {STAGES.map(({ key }) => (
            <SkeletonBar key={key} className="h-7 w-full" />
          ))}
        </div>
      </StatsCard>
    );
  }

  if (!stage) return null;

  const base = stage.receipt_count || 1;
  const rows = STAGES.map(({ key, label, opacity }) => ({
    label,
    opacity,
    count: stage[key],
    pct: Math.round((stage[key] / base) * 100),
  }));

  return (
    <StatsCard title="입법 진행 단계" icon="filter_alt" subtitle="접수 대비 도달률" delay={0.05}>
      <ChartContainer config={chartConfig} className="aspect-auto h-[190px] w-full">
        <BarChart data={rows} layout="vertical" margin={{ left: 0, right: 44, top: 0, bottom: 0 }}>
          <XAxis type="number" hide domain={[0, base]} />
          <YAxis type="category" dataKey="label" tickLine={false} axisLine={false} width={78} tick={{ fontSize: 12 }} />
          <ChartTooltip
            cursor={false}
            content={
              <ChartTooltipContent
                hideIndicator
                formatter={(value, _name, item) => (
                  <div className="flex w-full items-center justify-between gap-3">
                    <span className="text-gray-2 dark:text-gray-1">{item.payload.label}</span>
                    <span className="font-mono font-medium tabular-nums text-primary-3 dark:text-gray-0.5">
                      {Number(value).toLocaleString()}건 · {item.payload.pct}%
                    </span>
                  </div>
                )}
              />
            }
          />
          <Bar dataKey="count" radius={[4, 8, 8, 4]} background={{ fill: 'transparent' }} barSize={26}>
            {rows.map((row) => (
              <Cell key={row.label} fill={STAGE_BLUE} fillOpacity={row.opacity} />
            ))}
            <LabelList
              dataKey="pct"
              position="right"
              formatter={(value) => `${Number(value)}%`}
              className="fill-gray-3 dark:fill-gray-1"
              fontSize={11}
              fontWeight={600}
            />
          </Bar>
        </BarChart>
      </ChartContainer>
    </StatsCard>
  );
}
