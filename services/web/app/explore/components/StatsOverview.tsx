'use client';

import { useEffect, useRef } from 'react';
import { animate, motion, useInView, useReducedMotion } from 'framer-motion';
import { useGetStatisticsOverview } from '../apis';
import { SkeletonBar } from './StatsSkeleton';

interface CountUpProps {
  value: number;
  decimals?: number;
}

/** 뷰포트 진입 시 0→값 카운트업 텍스트(reduced-motion이면 즉시 표시). */
function CountUp({ value, decimals = 0 }: CountUpProps) {
  const ref = useRef<HTMLSpanElement>(null);
  const inView = useInView(ref, { once: true });
  const reduceMotion = useReducedMotion();

  useEffect(() => {
    const node = ref.current;
    if (!node || !inView) return undefined;

    const format = (v: number) => (decimals > 0 ? v.toFixed(decimals) : Math.round(v).toLocaleString());

    if (reduceMotion) {
      node.textContent = format(value);
      return undefined;
    }

    const controls = animate(0, value, {
      duration: 1.1,
      ease: [0.16, 1, 0.3, 1],
      onUpdate: (v) => {
        node.textContent = format(v);
      },
    });
    return () => controls.stop();
  }, [inView, value, decimals, reduceMotion]);

  return <span ref={ref}>0</span>;
}

/** 가결률 미니 링(SVG stroke 애니메이션). */
function PassRateRing({ rate }: { rate: number }) {
  const reduceMotion = useReducedMotion();
  const R = 15;
  const C = 2 * Math.PI * R;
  const target = C * (1 - Math.min(rate, 100) / 100);

  return (
    <svg viewBox="0 0 36 36" className="h-10 w-10 -rotate-90" aria-hidden>
      <circle cx="18" cy="18" r={R} fill="none" strokeWidth="4" className="stroke-gray-0.5 dark:stroke-dark-l" />
      <motion.circle
        cx="18"
        cy="18"
        r={R}
        fill="none"
        className="stroke-primary-3 dark:stroke-gray-0.5"
        strokeWidth="4"
        strokeLinecap="round"
        strokeDasharray={C}
        initial={reduceMotion ? { strokeDashoffset: target } : { strokeDashoffset: C }}
        whileInView={{ strokeDashoffset: target }}
        viewport={{ once: true }}
        transition={{ duration: 1.1, ease: [0.16, 1, 0.3, 1], delay: 0.2 }}
      />
    </svg>
  );
}

/** KPI 카드 4종 — 총 발의 / 가결 / 계류 중 / 가결률(링 게이지 포함). */
export default function StatsOverview() {
  const { data, isLoading } = useGetStatisticsOverview();
  const reduceMotion = useReducedMotion();
  const overview = data?.data;

  if (isLoading) {
    return (
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {[0, 1, 2, 3].map((i) => (
          <div
            key={i}
            className="rounded-2xl border border-gray-1 bg-white p-4 shadow-sm dark:border-dark-l dark:bg-dark-b">
            <SkeletonBar className="h-3 w-14" />
            <SkeletonBar className="mt-2.5 h-6 w-20" />
          </div>
        ))}
      </div>
    );
  }

  if (!overview) return null;

  const cards = [
    { label: '총 발의', value: overview.total_count, unit: '건', icon: 'stacks' },
    { label: '가결', value: overview.passed_count, unit: '건', icon: 'task_alt' },
    { label: '계류 중', value: overview.pending_count, unit: '건', icon: 'hourglass_top' },
    { label: '가결률', value: overview.pass_rate, unit: '%', icon: 'percent', decimals: 1 },
  ];

  return (
    <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
      {cards.map((card, i) => (
        <motion.div
          key={card.label}
          initial={reduceMotion ? false : { opacity: 0, y: 14 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.45, delay: i * 0.07, ease: [0.22, 1, 0.36, 1] }}
          className="rounded-2xl border border-gray-1 bg-white p-4 shadow-sm dark:border-dark-l dark:bg-dark-b">
          <div className="flex items-start justify-between gap-2">
            <div>
              <p className="flex items-center gap-1 text-[12px] text-gray-2">
                <span className="material-symbols-outlined text-[14px]">{card.icon}</span>
                {card.label}
              </p>
              <p className="mt-1.5 text-[24px] font-bold leading-none text-primary-3 dark:text-gray-0.5">
                <CountUp value={card.value} decimals={card.decimals ?? 0} />
                <span className="ml-0.5 text-[13px] font-medium text-gray-2">{card.unit}</span>
              </p>
            </div>
            {card.label === '가결률' && <PassRateRing rate={overview.pass_rate} />}
          </div>
        </motion.div>
      ))}
    </div>
  );
}
