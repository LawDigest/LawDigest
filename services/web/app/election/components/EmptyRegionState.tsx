'use client';

import { Button, Card, CardBody } from '@nextui-org/react';

interface EmptyRegionStateProps {
  title: string;
  description: string;
  isPending?: boolean;
  onResolve: () => void;
  onManualSelect: () => void;
}

export default function EmptyRegionState({
  title,
  description,
  isPending = false,
  onResolve,
  onManualSelect,
}: EmptyRegionStateProps) {
  return (
    <Card className="border border-dashed border-default-300 bg-transparent">
      <CardBody className="flex min-h-[240px] flex-col items-center justify-center gap-4 p-8 text-center">
        <div className="space-y-2">
          <h2 className="text-xl font-semibold">{title}</h2>
          <p className="max-w-[440px] text-sm leading-6 text-gray-500">{description}</p>
        </div>
        <div className="flex flex-col gap-3 sm:flex-row">
          <Button color="default" className="font-medium" isLoading={isPending} onClick={onResolve}>
            현재 위치로 지역 찾기
          </Button>
          <Button variant="bordered" className="font-medium" onClick={onManualSelect}>
            직접 지역 선택
          </Button>
        </div>
      </CardBody>
    </Card>
  );
}
