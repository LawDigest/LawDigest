'use client';

import { useState } from 'react';
import clsx from 'clsx';
import { Area, AreaChart, CartesianGrid, XAxis, YAxis } from 'recharts';
import {
  ChartConfig,
  ChartContainer,
  ChartLegend,
  ChartLegendContent,
  ChartTooltip,
  ChartTooltipContent,
} from '@/components/ui/chart';
import { useGetStatisticsTrend, useGetStatisticsTrendDetail } from '../apis';
import StatsCard from './StatsCard';

const PERIODS = [
  { months: 6, label: '6개월' },
  { months: 12, label: '12개월' },
  { months: 24, label: '전체' },
] as const;

const chartConfig = {
  proposed: { label: '발의', color: '#0088ff' },
  passed: { label: '가결', color: '#16A34A' },
} satisfies ChartConfig;

/** 'YYYY-MM' → '7월' / 연도가 바뀌는 첫 달은 '25년 1월'. */
const formatMonth = (month: string, index: number, all: string[]) => {
  const [year, m] = month.split('-');
  const prev = index > 0 ? all[index - 1] : undefined;
  const monthLabel = `${Number(m)}월`;
  if (index === 0 || (prev && prev.slice(0, 4) !== year)) {
    return `${year.slice(2)}년 ${monthLabel}`;
  }
  return monthLabel;
};

/** 월별 발의·가결 추이 — 기간 전환 가능한 인터랙티브 영역 차트. */
export default function StatsTrendArea() {
  const [months, setMonths] = useState<number>(12);
  const detail = useGetStatisticsTrendDetail(months);
  // 신규 API 미배포 환경 폴백: 기존 /statistics/trend(발의 건수만)로 대체한다.
  const fallback = useGetStatisticsTrend(months);

  const detailPoints = detail.data?.data ?? [];
  const hasDetail = !detail.isError && detailPoints.length > 0;

  const points = hasDetail
    ? detailPoints.map((p) => ({ month: p.month, proposed: p.proposed_count, passed: p.passed_count }))
    : (fallback.data?.data ?? []).map((p) => ({ month: p.month, proposed: p.count }));

  if (points.length === 0) return null;

  const monthKeys = points.map((p) => p.month);

  return (
    <StatsCard
      title="월별 발의·가결 추이"
      icon="show_chart"
      subtitle={
        <span className="flex gap-1" role="tablist" aria-label="조회 기간">
          {PERIODS.map((period) => (
            <button
              key={period.months}
              type="button"
              role="tab"
              aria-selected={months === period.months}
              onClick={() => setMonths(period.months)}
              className={clsx(
                'cursor-pointer rounded-full px-2.5 py-1 text-[11px] font-medium transition-colors duration-200',
                months === period.months
                  ? 'bg-primary-3 text-white dark:bg-gray-0.5 dark:text-primary-3'
                  : 'bg-gray-0.5 text-gray-3 hover:bg-gray-1 dark:bg-dark-l dark:text-gray-1',
              )}>
              {period.label}
            </button>
          ))}
        </span>
      }>
      <ChartContainer config={chartConfig} className="aspect-auto h-[220px] w-full">
        <AreaChart data={points} margin={{ left: 4, right: 12, top: 8 }}>
          <defs>
            <linearGradient id="fillProposed" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="var(--color-proposed)" stopOpacity={0.5} />
              <stop offset="95%" stopColor="var(--color-proposed)" stopOpacity={0.05} />
            </linearGradient>
            <linearGradient id="fillPassed" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="var(--color-passed)" stopOpacity={0.5} />
              <stop offset="95%" stopColor="var(--color-passed)" stopOpacity={0.05} />
            </linearGradient>
          </defs>
          <CartesianGrid vertical={false} strokeDasharray="3 3" />
          <XAxis
            dataKey="month"
            tickLine={false}
            axisLine={false}
            tickMargin={8}
            minTickGap={24}
            tickFormatter={(value: string, index: number) => formatMonth(value, index, monthKeys)}
          />
          <YAxis tickLine={false} axisLine={false} width={36} tickFormatter={(v: number) => v.toLocaleString()} />
          <ChartTooltip
            cursor={{ strokeDasharray: '3 3' }}
            content={
              <ChartTooltipContent
                indicator="dot"
                labelFormatter={(_, payload) => {
                  const month = payload?.[0]?.payload?.month as string | undefined;
                  if (!month) return '';
                  const [year, m] = month.split('-');
                  return `${year}년 ${Number(m)}월`;
                }}
              />
            }
          />
          {hasDetail && (
            <Area
              dataKey="passed"
              type="monotone"
              fill="url(#fillPassed)"
              stroke="var(--color-passed)"
              strokeWidth={2}
              activeDot={{ r: 4 }}
            />
          )}
          <Area
            dataKey="proposed"
            type="monotone"
            fill="url(#fillProposed)"
            stroke="var(--color-proposed)"
            strokeWidth={2}
            activeDot={{ r: 4 }}
          />
          {hasDetail && <ChartLegend content={<ChartLegendContent />} />}
        </AreaChart>
      </ChartContainer>
    </StatsCard>
  );
}
