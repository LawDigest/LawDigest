'use client';

import { useMemo } from 'react';

interface ElectionHeaderProps {
  electionName: string;
  electionDate: Date;
}

function calcDday(electionDate: Date): number {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const target = new Date(electionDate);
  target.setHours(0, 0, 0, 0);
  return Math.ceil((target.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
}

function getDdayLabel(dday: number): string {
  if (dday === 0) return 'D-DAY';
  if (dday > 0) return `D-${dday}`;
  return `D+${Math.abs(dday)}`;
}

function getDdayColor(dday: number): string {
  if (dday <= 0) return 'bg-theme-alert text-white';
  if (dday <= 7) return 'bg-primary-2 text-white';
  return 'bg-gray-1 text-gray-4';
}

function formatDate(date: Date): string {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, '0');
  const d = String(date.getDate()).padStart(2, '0');
  return `${y}.${m}.${d}`;
}

export default function ElectionHeader({ electionName, electionDate }: ElectionHeaderProps) {
  const dday = useMemo(() => calcDday(electionDate), [electionDate]);
  const dateLabel = useMemo(() => formatDate(electionDate), [electionDate]);

  const ddayLabel = getDdayLabel(dday);
  const ddayColor = getDdayColor(dday);

  return (
    <header className="flex items-start justify-between gap-4 px-5 pt-6 pb-4">
      <div className="flex flex-col gap-1">
        <p className="text-xs font-medium tracking-widest text-gray-2 uppercase">선거</p>
        <h1 className="text-2xl font-bold leading-snug text-gray-4 dark:text-white">{electionName}</h1>
      </div>
      <div className="flex flex-col items-center gap-0.5 shrink-0" aria-label={`선거까지 ${ddayLabel}`}>
        <span className="tabular-nums" style={{ color: ddayColor }}>
          <span className="text-2xl font-thin">D-</span>
          <span className="text-4xl font-black">{dday <= 0 ? Math.abs(dday) : dday}</span>
        </span>
        <span className="text-xs font-semibold text-gray-3 tabular-nums">{dateLabel}</span>
      </div>
    </header>
  );
}
