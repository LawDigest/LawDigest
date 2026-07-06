'use client';

import { Bar, BarChart, LabelList, XAxis, YAxis } from 'recharts';
import { ChartConfig, ChartContainer, ChartTooltip, ChartTooltipContent } from '@/components/ui/chart';
import { useGetStatisticsByCommittee } from '../apis';
import StatsCard from './StatsCard';

const TOP_N = 8;

const chartConfig = {
  count: { label: '접수 법안', color: '#96BCFA' },
} satisfies ChartConfig;

/** 소관 위원회별 법안 수 상위 N — 가로 막대. */
export default function StatsCommitteeBars() {
  const { data, isError } = useGetStatisticsByCommittee();
  const committees = data?.data ?? [];

  // 신규 API 미배포 환경에서는 카드 자체를 숨긴다.
  if (isError || committees.length === 0) return null;

  const rows = committees.slice(0, TOP_N).map((c) => ({
    // '위원회' 접미사를 줄여 축 라벨을 짧게 유지한다(툴팁에는 전체 이름 표시).
    name: c.committee.replace(/위원회$/, ''),
    fullName: c.committee,
    count: c.count,
    passed: c.passed_count,
  }));

  return (
    <StatsCard title="위원회별 접수 현황" icon="account_balance" subtitle={`상위 ${rows.length}개`} delay={0.15}>
      <ChartContainer config={chartConfig} className="aspect-auto w-full" style={{ height: rows.length * 30 + 8 }}>
        <BarChart data={rows} layout="vertical" margin={{ left: 0, right: 42, top: 0, bottom: 0 }}>
          <XAxis type="number" hide />
          <YAxis
            type="category"
            dataKey="name"
            tickLine={false}
            axisLine={false}
            width={96}
            tick={{ fontSize: 11 }}
            tickFormatter={(name: string) => (name.length > 8 ? `${name.slice(0, 8)}…` : name)}
          />
          <ChartTooltip
            cursor={false}
            content={
              <ChartTooltipContent
                hideIndicator
                labelFormatter={(_, payload) => payload?.[0]?.payload?.fullName ?? ''}
                formatter={(value, _name, item) => (
                  <div className="flex w-full flex-col gap-1">
                    <span className="flex justify-between gap-3 text-gray-2 dark:text-gray-1">
                      접수
                      <b className="font-mono tabular-nums text-primary-3 dark:text-gray-0.5">
                        {Number(value).toLocaleString()}건
                      </b>
                    </span>
                    <span className="flex justify-between gap-3 text-gray-2 dark:text-gray-1">
                      가결
                      <b className="font-mono tabular-nums text-primary-3 dark:text-gray-0.5">
                        {Number(item.payload.passed).toLocaleString()}건
                      </b>
                    </span>
                  </div>
                )}
              />
            }
          />
          <Bar dataKey="count" fill="var(--color-count)" radius={[3, 6, 6, 3]} barSize={16}>
            <LabelList
              dataKey="count"
              position="right"
              formatter={(value: number) => value.toLocaleString()}
              className="fill-gray-3 dark:fill-gray-1"
              fontSize={11}
            />
          </Bar>
        </BarChart>
      </ChartContainer>
    </StatsCard>
  );
}
