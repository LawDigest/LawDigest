'use client';

import { Button, Card, CardBody, Chip } from '@nextui-org/react';
import { ElectionRegionCode, ElectionRegionType } from '@/types';
import { getRegionTypeLabel } from '../utils/electionLabels';

interface RegionConfirmCardProps {
  regionName: string | null;
  regionCode: ElectionRegionCode | null;
  regionType: ElectionRegionType | null;
  isPending?: boolean;
  onConfirm: () => void;
  onManualSelect: () => void;
}

export default function RegionConfirmCard({
  regionName,
  regionCode,
  regionType,
  isPending = false,
  onConfirm,
  onManualSelect,
}: RegionConfirmCardProps) {
  return (
    <Card className="border border-default-200 bg-transparent">
      <CardBody className="flex flex-col gap-5 p-6">
        <div className="space-y-2">
          <p className="text-sm font-medium text-gray-500">추천 지역 확인</p>
          <h2 className="text-2xl font-semibold">{regionName ?? '추천 지역을 확인해주세요.'}</h2>
          <p className="text-sm leading-6 text-gray-500">
            현재 위치를 기준으로 가장 가까운 선거 지역을 찾았습니다. 맞다면 그대로 확정하고, 아니면 수동으로 수정할 수
            있습니다.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          {regionType ? <Chip variant="flat">{getRegionTypeLabel(regionType)}</Chip> : null}
          {regionCode ? <Chip variant="bordered">{regionCode}</Chip> : null}
        </div>
        <div className="flex flex-col gap-3 sm:flex-row">
          <Button color="default" className="font-medium" isLoading={isPending} onClick={onConfirm}>
            이 지역으로 확정
          </Button>
          <Button variant="bordered" className="font-medium" onClick={onManualSelect}>
            직접 수정
          </Button>
        </div>
      </CardBody>
    </Card>
  );
}
