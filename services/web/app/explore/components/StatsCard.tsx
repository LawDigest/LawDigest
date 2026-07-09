'use client';

import { ReactNode } from 'react';
import clsx from 'clsx';
import { motion, useReducedMotion } from 'framer-motion';

interface StatsCardProps {
  title: string;
  subtitle?: ReactNode;
  icon?: string;
  delay?: number;
  className?: string;
  children: ReactNode;
}

/** 통계 카드 공용 셸 — 뷰포트 진입 시 fade-up 등장(reduced-motion 존중). */
export default function StatsCard({ title, subtitle, icon, delay = 0, className, children }: StatsCardProps) {
  const reduceMotion = useReducedMotion();

  return (
    <motion.section
      initial={reduceMotion ? false : { opacity: 0, y: 18 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-40px' }}
      transition={{ duration: 0.5, delay, ease: [0.22, 1, 0.36, 1] }}
      className={clsx(
        'rounded-2xl border border-gray-1 bg-white p-4 shadow-sm dark:border-dark-l dark:bg-dark-b',
        className,
      )}>
      <div className="mb-3 flex items-baseline justify-between gap-2">
        <h2 className="flex items-center gap-1.5 text-[14px] font-bold text-primary-3 dark:text-gray-0.5">
          {icon && <span className="material-symbols-outlined text-[17px] text-gray-2">{icon}</span>}
          {title}
        </h2>
        {subtitle && <span className="shrink-0 text-[12px] text-gray-2">{subtitle}</span>}
      </div>
      {children}
    </motion.section>
  );
}
