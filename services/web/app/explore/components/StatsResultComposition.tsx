'use client';

import { Bar, BarChart, XAxis, YAxis } from 'recharts';
import { ChartConfig, ChartContainer, ChartTooltip, ChartTooltipContent } from '@/components/ui/chart';
import { useGetStatisticsResultBreakdown } from '../apis';
import StatsCard from './StatsCard';
import { SkeletonBar } from './StatsSkeleton';

/**
 * 알려진 처리 결과별 색 — 디자인 토큰 기반(Neutral First).
 * 가결 계열=soft assembly blue, 폐기·철회=회색 사다리, 부결=alert-red, 계류(미결정)=quiet divider.
 */
const RESULT_COLORS: Record<string, string> = {
  원안가결: '#96BCFA',
  수정가결: '#96BCFA99',
  대안반영폐기: '#999999',
  수정안반영폐기: '#99999999',
  폐기: '#99999966',
  철회: '#555555',
  부결: '#E63946',
  계류: '#E0E0E0',
};
const EXTRA_PALETTE = ['#99999980', '#55555580', '#96BCFA80', '#E0E0E080'];

/** 처리 결과 구성 — 100% 스택 단일 막대 + 범례. */
export default function StatsResultComposition() {
  const { data, isError, isLoading } = useGetStatisticsResultBreakdown();
  const rows = data?.data ?? [];

  if (isLoading) {
    return (
      <StatsCard title="처리 결과 구성" icon="data_usage" delay={0.1}>
        <SkeletonBar className="h-[52px] w-full" />
        <div className="mt-3 grid grid-cols-2 gap-x-3 gap-y-1.5">
          {Array.from({ length: 4 }, (_, i) => (
            <SkeletonBar key={i} className="h-3 w-full" />
          ))}
        </div>
      </StatsCard>
    );
  }

  // 신규 API 미배포 환경에서는 카드 자체를 숨긴다.
  if (isError || rows.length === 0) return null;

  const total = rows.reduce((sum, r) => sum + r.count, 0) || 1;
  const unknownResults = rows.filter((r) => !RESULT_COLORS[r.result]).map((r) => r.result);
  const segments = rows.map((r) => ({
    result: r.result,
    count: r.count,
    color: RESULT_COLORS[r.result] ?? EXTRA_PALETTE[unknownResults.indexOf(r.result) % EXTRA_PALETTE.length],
  }));

  const composition = segments.reduce<Record<string, number | string>>(
    (acc, seg) => {
      acc[seg.result] = seg.count;
      return acc;
    },
    { name: '처리 결과' },
  );

  const chartConfig = segments.reduce<Record<string, { label: string; color: string }>>((acc, seg) => {
    acc[seg.result] = { label: seg.result, color: seg.color };
    return acc;
  }, {}) satisfies ChartConfig;

  return (
    <StatsCard title="처리 결과 구성" icon="data_usage" subtitle={`${total.toLocaleString()}건 기준`} delay={0.1}>
      <ChartContainer config={chartConfig} className="aspect-auto h-[52px] w-full">
        <BarChart data={[composition]} layout="vertical" margin={{ left: 0, right: 0, top: 4, bottom: 4 }}>
          <XAxis type="number" hide />
          <YAxis type="category" dataKey="name" hide />
          <ChartTooltip cursor={false} content={<ChartTooltipContent hideLabel className="min-w-[11rem]" />} />
          {segments.map((seg, i) => {
            const isFirst = i === 0;
            const isLast = i === segments.length - 1;
            let radius: number | [number, number, number, number] = 0;
            if (isFirst && isLast) radius = 6;
            else if (isFirst) radius = [6, 0, 0, 6];
            else if (isLast) radius = [0, 6, 6, 0];
            return <Bar key={seg.result} dataKey={seg.result} stackId="results" fill={seg.color} radius={radius} />;
          })}
        </BarChart>
      </ChartContainer>
      <div className="mt-3 grid grid-cols-2 gap-x-3 gap-y-1.5 text-[12px]">
        {segments.map((seg) => (
          <span key={seg.result} className="flex items-center gap-1.5 text-gray-3 dark:text-gray-1">
            <span className="h-2.5 w-2.5 shrink-0 rounded-sm" style={{ background: seg.color }} />
            <span className="truncate">{seg.result}</span>
            <b className="ml-auto shrink-0 tabular-nums text-primary-3 dark:text-gray-0.5">
              {((seg.count / total) * 100).toFixed(1)}%
            </b>
          </span>
        ))}
      </div>
    </StatsCard>
  );
}
