'use client';

import { useState } from 'react';
import KoreaMap, { MAP_REGIONS } from './KoreaMap';

export default function MapRegionCarousel() {
  const [regionIndex, setRegionIndex] = useState(0);
  const region = MAP_REGIONS[regionIndex];

  return (
    <div className="flex flex-col gap-3">
      {/* 지도 */}
      <KoreaMap regionIndex={regionIndex} onRegionChange={setRegionIndex} />

      {/* 권역 라벨 + 페이지 인디케이터 */}
      <div className="flex items-center justify-between px-1">
        <div className="flex items-center gap-2">
          <span className="text-sm font-bold text-gray-4 dark:text-white">{region.label}</span>
          <span className="text-xs text-gray-2">
            {regionIndex === 0 ? '전국' : `${regionIndex} / ${MAP_REGIONS.length - 1}`}
          </span>
        </div>
        {/* 도트 인디케이터 */}
        <div className="flex items-center gap-1">
          {MAP_REGIONS.map((r, i) => (
            <button
              key={r.key}
              type="button"
              aria-label={r.label}
              onClick={() => setRegionIndex(i)}
              className={[
                'rounded-full transition-all',
                i === regionIndex ? 'w-4 h-1.5 bg-gray-4 dark:bg-white' : 'w-1.5 h-1.5 bg-gray-1 dark:bg-dark-l',
              ].join(' ')}
            />
          ))}
        </div>
      </div>

      {/* 스와이프 힌트 (첫 방문 시) */}
      {regionIndex === 0 && (
        <p className="text-center text-xs text-gray-2 opacity-60">← 좌우로 밀어 권역을 이동하세요 →</p>
      )}
    </div>
  );
}
