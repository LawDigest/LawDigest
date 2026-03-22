'use client';

import { useState } from 'react';
import { IconArrowDown, IconArrowUp } from '@/public/svgs';

interface ExpandableListProps {
  items: React.ReactNode[];
  initialCount: number;
}

export default function ExpandableList({ items, initialCount }: ExpandableListProps) {
  const [visibleCount, setVisibleCount] = useState(initialCount);

  const hasMoreItems = visibleCount < items.length;

  return (
    <div className="flex flex-col gap-4">
      <div className="grid grid-cols-4 gap-y-4 xl:grid-cols-12 lg:grid-cols-10 md:grid-cols-8">
        {items.slice(0, visibleCount)}
      </div>

      {items.length > initialCount && (
        <div className="flex justify-center">
          {hasMoreItems ? (
            <button
              type="button"
              onClick={() => setVisibleCount(items.length)}
              className="flex items-center gap-2 px-4 py-2 text-sm font-semibold bg-gray-100 rounded-lg shadow dark:bg-gray-800">
              더 보기 <IconArrowDown />
            </button>
          ) : (
            <button
              type="button"
              onClick={() => setVisibleCount(initialCount)}
              className="flex items-center gap-2 px-4 py-2 text-sm font-semibold bg-gray-100 rounded-lg shadow dark:bg-gray-800">
              줄이기 <IconArrowUp />
            </button>
          )}
        </div>
      )}
    </div>
  );
}
