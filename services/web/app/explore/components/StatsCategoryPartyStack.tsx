'use client';

import { useMemo } from 'react';
import { Bar, BarChart, CartesianGrid, XAxis, YAxis } from 'recharts';
import { getCategoryMeta } from '@/config/categories';
import { getPartyColor } from '@/constants/party';
import {
  ChartConfig,
  ChartContainer,
  ChartLegend,
  ChartLegendContent,
  ChartTooltip,
  ChartTooltipContent,
} from '@/components/ui/chart';
import { useGetStatisticsCategoryParty } from '../apis';
import StatsCard from './StatsCard';

const TOP_CATEGORIES = 6;
const TOP_PARTIES = 4;
const ETC_KEY = '기타';
const ETC_COLOR = '#B3B3B3';

/** 분야×정당 구성 — 상위 분야별로 정당 스택 세로 막대. */
export default function StatsCategoryPartyStack() {
  const { data, isError } = useGetStatisticsCategoryParty();
  const cells = useMemo(() => data?.data ?? [], [data]);

  const { rows, parties } = useMemo(() => {
    if (cells.length === 0) return { rows: [], parties: [] as string[] };

    const categoryTotals = new Map<string, number>();
    const partyTotals = new Map<string, number>();
    cells.forEach((cell) => {
      if (!cell.category || cell.category === 'unknown') return;
      categoryTotals.set(cell.category, (categoryTotals.get(cell.category) ?? 0) + cell.count);
      partyTotals.set(cell.party_name, (partyTotals.get(cell.party_name) ?? 0) + cell.count);
    });

    const topCategories = [...categoryTotals.entries()]
      .sort((a, b) => b[1] - a[1])
      .slice(0, TOP_CATEGORIES)
      .map(([category]) => category);
    const topParties = [...partyTotals.entries()]
      .sort((a, b) => b[1] - a[1])
      .slice(0, TOP_PARTIES)
      .map(([party]) => party);

    const pivoted = topCategories.map((category) => {
      const row: Record<string, number | string> = {
        category,
        label: getCategoryMeta(category).label,
        [ETC_KEY]: 0,
      };
      topParties.forEach((party) => {
        row[party] = 0;
      });
      cells
        .filter((cell) => cell.category === category)
        .forEach((cell) => {
          const key = topParties.includes(cell.party_name) ? cell.party_name : ETC_KEY;
          row[key] = ((row[key] as number) ?? 0) + cell.count;
        });
      return row;
    });

    return { rows: pivoted, parties: topParties };
  }, [cells]);

  // 신규 API 미배포 환경에서는 카드 자체를 숨긴다.
  if (isError || rows.length === 0) return null;

  const stackKeys = [...parties, ETC_KEY];
  const chartConfig = stackKeys.reduce<Record<string, { label: string; color: string }>>((acc, key) => {
    acc[key] = { label: key, color: key === ETC_KEY ? ETC_COLOR : getPartyColor(key) };
    return acc;
  }, {}) satisfies ChartConfig;

  return (
    <StatsCard title="분야별 정당 구성" icon="stacked_bar_chart" subtitle={`상위 ${rows.length}개 분야`} delay={0.2}>
      <ChartContainer config={chartConfig} className="aspect-auto h-[240px] w-full">
        <BarChart data={rows} margin={{ left: 4, right: 4, top: 8 }}>
          <CartesianGrid vertical={false} strokeDasharray="3 3" />
          <XAxis
            dataKey="label"
            tickLine={false}
            axisLine={false}
            tickMargin={6}
            interval={0}
            tick={{ fontSize: 10 }}
            tickFormatter={(label: string) => (label.length > 5 ? `${label.slice(0, 5)}…` : label)}
          />
          <YAxis tickLine={false} axisLine={false} width={36} tickFormatter={(v: number) => v.toLocaleString()} />
          <ChartTooltip
            content={<ChartTooltipContent labelFormatter={(_, payload) => payload?.[0]?.payload?.label ?? ''} />}
          />
          {stackKeys.map((key, i) => (
            <Bar
              key={key}
              dataKey={key}
              stackId="parties"
              fill={key === ETC_KEY ? ETC_COLOR : getPartyColor(key)}
              radius={i === stackKeys.length - 1 ? [4, 4, 0, 0] : 0}
              maxBarSize={36}
            />
          ))}
          <ChartLegend content={<ChartLegendContent />} />
        </BarChart>
      </ChartContainer>
    </StatsCard>
  );
}
