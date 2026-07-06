'use client';

import { Bar, BarChart, Cell, XAxis, YAxis } from 'recharts';
import { getPartyColor } from '@/constants/party';
import { ChartConfig, ChartContainer, ChartTooltip, ChartTooltipContent } from '@/components/ui/chart';
import { useGetStatisticsByParty, useGetStatisticsPartyPerformance } from '../apis';
import StatsCard from './StatsCard';

const TOP_N = 8;

const chartConfig = {
  passed: { label: '가결' },
  pending: { label: '미가결·계류' },
} satisfies ChartConfig;

/** 정당별 발의·가결 실적 — 정당색 스택 가로 막대(가결=진하게, 나머지=연하게). */
export default function StatsPartyPerformance() {
  const performance = useGetStatisticsPartyPerformance();
  // 신규 API 미배포 환경 폴백: 기존 /statistics/by-party(발의 건수만)로 대체한다.
  const fallback = useGetStatisticsByParty();

  const perfRows = performance.data?.data ?? [];
  const hasPerformance = !performance.isError && perfRows.length > 0;

  const rows = hasPerformance
    ? perfRows.slice(0, TOP_N).map((p) => ({
        name: p.party_name,
        color: getPartyColor(p.party_name),
        passed: p.passed_count,
        pending: p.count - p.passed_count,
        total: p.count,
        passRate: p.pass_rate,
      }))
    : (fallback.data?.data ?? []).slice(0, TOP_N).map((p) => ({
        name: p.party_name,
        color: getPartyColor(p.party_name),
        passed: 0,
        pending: p.count,
        total: p.count,
        passRate: null as number | null,
      }));

  if (rows.length === 0) return null;

  return (
    <StatsCard
      title="정당별 발의·가결"
      icon="flag"
      subtitle={hasPerformance ? '진한 색 = 가결' : undefined}
      delay={0.1}>
      <ChartContainer config={chartConfig} className="aspect-auto w-full" style={{ height: rows.length * 34 + 8 }}>
        <BarChart data={rows} layout="vertical" margin={{ left: 0, right: 48, top: 0, bottom: 0 }}>
          <XAxis type="number" hide />
          <YAxis
            type="category"
            dataKey="name"
            tickLine={false}
            axisLine={false}
            width={82}
            tick={{ fontSize: 11 }}
            tickFormatter={(name: string) => (name.length > 6 ? `${name.slice(0, 6)}…` : name)}
          />
          <ChartTooltip
            cursor={false}
            content={
              <ChartTooltipContent
                hideLabel
                hideIndicator
                formatter={(_value, name, item) => {
                  // 스택 막대라 항목이 2번 호출되므로 첫 항목(passed)에서만 전체 요약을 그린다.
                  if (name !== 'passed') return null;
                  const row = item.payload;
                  return (
                    <div className="flex min-w-[10rem] flex-col gap-1">
                      <span className="flex items-center gap-1.5 font-medium text-primary-3 dark:text-gray-0.5">
                        <span className="h-2.5 w-2.5 rounded-sm" style={{ background: row.color }} />
                        {row.name}
                      </span>
                      <span className="flex justify-between text-gray-2 dark:text-gray-1">
                        발의
                        <b className="font-mono tabular-nums text-primary-3 dark:text-gray-0.5">
                          {row.total.toLocaleString()}건
                        </b>
                      </span>
                      {row.passRate !== null && (
                        <span className="flex justify-between text-gray-2 dark:text-gray-1">
                          가결
                          <b className="font-mono tabular-nums text-primary-3 dark:text-gray-0.5">
                            {row.passed.toLocaleString()}건 · {row.passRate}%
                          </b>
                        </span>
                      )}
                    </div>
                  );
                }}
              />
            }
          />
          <Bar dataKey="passed" stackId="bills" radius={[4, 0, 0, 4]} barSize={18}>
            {rows.map((row) => (
              <Cell key={row.name} fill={row.color} />
            ))}
          </Bar>
          <Bar dataKey="pending" stackId="bills" radius={[0, 4, 4, 0]} barSize={18}>
            {rows.map((row) => (
              // 가결 데이터가 없는 폴백 모드에서는 전체 막대를 원색으로 채운다.
              <Cell key={row.name} fill={row.color} fillOpacity={hasPerformance ? 0.3 : 1} />
            ))}
          </Bar>
        </BarChart>
      </ChartContainer>
    </StatsCard>
  );
}
