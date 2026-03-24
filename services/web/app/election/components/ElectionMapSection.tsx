'use client';

import { useState } from 'react';
import { Button, ButtonGroup } from '@nextui-org/button';
import { ElectionId, ElectionRegionType, ElectionRegionCode, ElectionViewMode } from '@/types';
import { useGetElectionMap } from '../apis/queries';
import { Loading } from '@/components/common';

interface ElectionMapSectionProps {
  electionId: ElectionId;
  depth: ElectionRegionType;
  regionCode: ElectionRegionCode;
}

export default function ElectionMapSection({
  electionId,
  depth,
  regionCode,
}: ElectionMapSectionProps) {
  const [viewMode, setViewMode] = useState<ElectionViewMode>('geographic');
  const { data: mapData, isLoading } = useGetElectionMap(electionId, depth, regionCode, viewMode);

  return (
    <section className="flex flex-col gap-4 w-full h-full min-h-[400px] lg:min-h-[600px] bg-white dark:bg-dark-b rounded-lg border dark:border-dark-l p-4">
      <div className="flex items-center justify-between">
        <h3 className="font-bold text-lg">지도 보기</h3>
        
        {/* 실제 지도 / 카토그램 전환 버튼 */}
        <ButtonGroup size="sm" variant="bordered">
          <Button
            isSelected={viewMode === 'geographic'}
            onPress={() => setViewMode('geographic')}
            className={viewMode === 'geographic' ? 'bg-[#191919] text-white' : ''}
          >
            실제 지도
          </Button>
          <Button
            isSelected={viewMode === 'cartogram'}
            onPress={() => setViewMode('cartogram')}
            className={viewMode === 'cartogram' ? 'bg-[#191919] text-white' : ''}
          >
            카토그램
          </Button>
        </ButtonGroup>
      </div>

      <div className="relative flex-1 flex items-center justify-center border dark:border-dark-l rounded bg-gray-50 dark:bg-dark-l/10 overflow-hidden">
        {isLoading ? (
          <Loading />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-500">
            {/* 여기에 D3 지도 렌더링 로직이 들어갈 예정입니다. */}
            <p>[ {viewMode === 'geographic' ? '실제 지도' : '카토그램'} ] 렌더링 영역</p>
          </div>
        )}
      </div>

      {/* 범례 영역 (임시) */}
      <div className="flex gap-4 text-xs">
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 bg-primary-2 rounded-full" />
          <span>주요 정당</span>
        </div>
        <div className="flex items-center gap-1 text-gray-400 italic">
          * 색상은 정당별 공식 색상을 따릅니다.
        </div>
      </div>
    </section>
  );
}
