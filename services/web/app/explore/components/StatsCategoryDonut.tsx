'use client';

import { useMemo, useState } from 'react';
import clsx from 'clsx';
import { Cell, Label, Pie, PieChart, Sector } from 'recharts';
import type { PieSectorShapeProps } from 'recharts';
import { getCategoryMeta } from '@/config/categories';
import { ChartConfig, ChartContainer, ChartTooltip, ChartTooltipContent } from '@/components/ui/chart';
import { useGetStatisticsByCategory } from '../apis';
import StatsCard from './StatsCard';
import { SkeletonBar } from './StatsSkeleton';

const TOP_N = 6;
const ETC_COLOR = '#999999';

const chartConfig = {
  count: { label: '법안 수' },
} satisfies ChartConfig;

/** 분야별 분포 — 호버/범례 선택 시 조각이 확대되는 인터랙티브 도넛. */
export default function StatsCategoryDonut() {
  const { data, isLoading } = useGetStatisticsByCategory();
  const [activeIndex, setActiveIndex] = useState<number | null>(null);

  const raw = useMemo(() => (data?.data ?? []).filter((c) => c.category && c.category !== 'unknown'), [data]);

  if (isLoading) {
    return (
      <StatsCard title="분야별 분포" icon="donut_small" delay={0.15}>
        <div className="flex items-center gap-4">
          <SkeletonBar className="h-[168px] w-[168px] shrink-0 rounded-full" />
          <div className="grid flex-1 grid-cols-1 gap-2">
            {Array.from({ length: 5 }, (_, i) => (
              <SkeletonBar key={i} className="h-3 w-full" />
            ))}
          </div>
        </div>
      </StatsCard>
    );
  }

  const total = raw.reduce((sum, c) => sum + c.count, 0) || 1;
  const top = raw.slice(0, TOP_N);
  const restCount = raw.slice(TOP_N).reduce((sum, c) => sum + c.count, 0);

  const segments = [
    ...top.map((c) => ({
      name: getCategoryMeta(c.category).label,
      color: getCategoryMeta(c.category).color,
      count: c.count,
    })),
    ...(restCount > 0 ? [{ name: '기타', color: ETC_COLOR, count: restCount }] : []),
  ];

  if (raw.length === 0) return null;

  const active = activeIndex !== null ? segments[activeIndex] : null;

  return (
    <StatsCard title="분야별 분포" icon="donut_small" subtitle={`${raw.length}개 분야`} delay={0.15}>
      <div className="flex items-center gap-4">
        <ChartContainer config={chartConfig} className="aspect-square h-[168px] shrink-0">
          <PieChart>
            <ChartTooltip cursor={false} content={<ChartTooltipContent hideLabel nameKey="name" />} />
            <Pie
              data={segments}
              dataKey="count"
              nameKey="name"
              innerRadius={52}
              outerRadius={72}
              paddingAngle={2}
              strokeWidth={0}
              shape={({ outerRadius, isActive, index, ...props }: PieSectorShapeProps) => (
                <Sector {...props} outerRadius={outerRadius + (isActive || index === activeIndex ? 6 : 0)} />
              )}
              onMouseEnter={(_, index) => setActiveIndex(index)}
              onMouseLeave={() => setActiveIndex(null)}>
              {segments.map((seg) => (
                <Cell key={seg.name} fill={seg.color} className="cursor-pointer" />
              ))}
              <Label
                content={({ viewBox }) => {
                  if (!viewBox || !('cx' in viewBox) || !('cy' in viewBox)) return null;
                  const { cx, cy } = viewBox;
                  return (
                    <text x={cx} y={cy} textAnchor="middle" dominantBaseline="middle">
                      <tspan
                        x={cx}
                        y={(cy ?? 0) - 6}
                        className="fill-primary-3 text-[18px] font-bold dark:fill-gray-0.5">
                        {active ? `${Math.round((active.count / total) * 100)}%` : total.toLocaleString()}
                      </tspan>
                      <tspan x={cx} y={(cy ?? 0) + 12} className="fill-gray-2 text-[10px]">
                        {active ? active.name : '분류된 법안'}
                      </tspan>
                    </text>
                  );
                }}
              />
            </Pie>
          </PieChart>
        </ChartContainer>

        <div className="grid min-w-0 flex-1 grid-cols-1 gap-1">
          {segments.map((seg, i) => (
            <button
              key={seg.name}
              type="button"
              onMouseEnter={() => setActiveIndex(i)}
              onMouseLeave={() => setActiveIndex(null)}
              onFocus={() => setActiveIndex(i)}
              onBlur={() => setActiveIndex(null)}
              className={clsx(
                'flex cursor-pointer items-center gap-1.5 rounded-md px-1.5 py-0.5 text-left text-[12px] transition-colors duration-150',
                activeIndex === i
                  ? 'bg-gray-0.5 text-primary-3 dark:bg-dark-l dark:text-gray-0.5'
                  : 'text-gray-3 dark:text-gray-1',
              )}>
              <span className="h-2.5 w-2.5 shrink-0 rounded-sm" style={{ background: seg.color }} />
              <span className="truncate">{seg.name}</span>
              <b className="ml-auto shrink-0 tabular-nums text-primary-3 dark:text-gray-0.5">
                {Math.round((seg.count / total) * 100)}%
              </b>
            </button>
          ))}
        </div>
      </div>
    </StatsCard>
  );
}
