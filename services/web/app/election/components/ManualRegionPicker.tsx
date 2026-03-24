'use client';

import { useMemo, useState } from 'react';
import { Button, Card, CardBody } from '@nextui-org/react';
import { ElectionRegionType } from '@/types';

export interface ManualRegionFormValue {
  regionCode: string;
  regionName: string;
  regionType: ElectionRegionType;
}

interface ManualRegionPickerProps {
  initialValue?: ManualRegionFormValue;
  isPending?: boolean;
  onSubmit: (value: ManualRegionFormValue) => void;
  onCancel: () => void;
}

type ProvinceOption = {
  code: string;
  name: string;
};

const PROVINCES: ProvinceOption[] = [
  { code: '11', name: '서울특별시' },
  { code: '26', name: '부산광역시' },
  { code: '27', name: '대구광역시' },
  { code: '28', name: '인천광역시' },
  { code: '29', name: '광주광역시' },
  { code: '30', name: '대전광역시' },
  { code: '31', name: '울산광역시' },
  { code: '36', name: '세종특별자치시' },
  { code: '41', name: '경기도' },
  { code: '42', name: '강원특별자치도' },
  { code: '43', name: '충청북도' },
  { code: '44', name: '충청남도' },
  { code: '45', name: '전북특별자치도' },
  { code: '46', name: '전라남도' },
  { code: '47', name: '경상북도' },
  { code: '48', name: '경상남도' },
  { code: '50', name: '제주특별자치도' },
];

const inferProvinceCode = (initialValue?: ManualRegionFormValue) => {
  if (!initialValue) {
    return '11';
  }

  const matchedByPrefix = PROVINCES.find(({ code }) => initialValue.regionCode.startsWith(code));
  if (matchedByPrefix) {
    return matchedByPrefix.code;
  }

  const matchedByName = PROVINCES.find(({ name }) => initialValue.regionName.includes(name));
  if (matchedByName) {
    return matchedByName.code;
  }

  return '11';
};

export default function ManualRegionPicker({
  initialValue,
  isPending = false,
  onSubmit,
  onCancel,
}: ManualRegionPickerProps) {
  const defaultMode = initialValue?.regionType === 'NATIONAL' ? 'NATIONAL' : 'PROVINCE';
  const [selectionMode, setSelectionMode] = useState<ElectionRegionType>(defaultMode);
  const [selectedProvinceCode, setSelectedProvinceCode] = useState(() => inferProvinceCode(initialValue));

  const selectedProvince = useMemo(
    () => PROVINCES.find(({ code }) => code === selectedProvinceCode) ?? PROVINCES[0],
    [selectedProvinceCode],
  );

  const submitValue = useMemo<ManualRegionFormValue>(() => {
    if (selectionMode === 'NATIONAL') {
      return {
        regionCode: '00',
        regionName: '대한민국',
        regionType: 'NATIONAL',
      };
    }

    return {
      regionCode: selectedProvince.code,
      regionName: selectedProvince.name,
      regionType: 'PROVINCE',
    };
  }, [selectedProvince, selectionMode]);

  return (
    <Card className="border border-default-200 bg-transparent">
      <CardBody className="space-y-6 p-5 md:p-6">
        <div className="space-y-2">
          <p className="text-sm font-medium text-gray-500">직접 지역 선택</p>
          <h2 className="text-2xl font-semibold">어디부터 선거 지도를 볼지 선택하세요.</h2>
          <p className="text-sm leading-6 text-gray-500">
            현재 위치를 사용할 수 없으면 전국 또는 시도 단위에서 시작할 수 있습니다. 선택을 마치면 같은 화면에서 지도를
            이어서 탐색할 수 있습니다.
          </p>
        </div>

        <div className="grid gap-3 md:grid-cols-2">
          <button
            type="button"
            className={`rounded-2xl border px-4 py-4 text-left transition ${
              selectionMode === 'PROVINCE'
                ? 'border-default-900 bg-default-100'
                : 'border-default-200 bg-transparent hover:border-default-400'
            }`}
            onClick={() => setSelectionMode('PROVINCE')}>
            <p className="text-sm font-semibold">시도부터 보기</p>
            <p className="mt-1 text-sm leading-6 text-gray-500">
              내가 사는 지역이 포함된 시도에서 시작한 뒤 지도에서 좁혀 봅니다.
            </p>
          </button>
          <button
            type="button"
            className={`rounded-2xl border px-4 py-4 text-left transition ${
              selectionMode === 'NATIONAL'
                ? 'border-default-900 bg-default-100'
                : 'border-default-200 bg-transparent hover:border-default-400'
            }`}
            onClick={() => setSelectionMode('NATIONAL')}>
            <p className="text-sm font-semibold">전국에서 보기</p>
            <p className="mt-1 text-sm leading-6 text-gray-500">
              전국 결과부터 훑어본 뒤 원하는 시도와 지역으로 내려갑니다.
            </p>
          </button>
        </div>

        {selectionMode === 'PROVINCE' ? (
          <div className="space-y-4">
            <div className="space-y-2">
              <p className="text-sm font-medium text-gray-500">빠른 선택</p>
              <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-4">
                {PROVINCES.map((province) => {
                  const isActive = province.code === selectedProvinceCode;

                  return (
                    <button
                      key={province.code}
                      type="button"
                      className={`rounded-2xl border px-3 py-3 text-sm font-medium transition ${
                        isActive
                          ? 'border-default-900 bg-default-100 text-black'
                          : 'border-default-200 bg-white/60 text-gray-600 hover:border-default-400 hover:text-black'
                      }`}
                      onClick={() => setSelectedProvinceCode(province.code)}>
                      {province.name}
                    </button>
                  );
                })}
              </div>
            </div>

            <div className="space-y-2">
              <span className="text-sm font-medium text-gray-500">시도 선택</span>
              <select
                id="manual-province-select"
                aria-label="시도 선택"
                className="h-12 w-full rounded-2xl border border-default-300 bg-transparent px-4 text-sm text-black outline-none transition focus:border-default-500"
                value={selectedProvinceCode}
                onChange={(event) => setSelectedProvinceCode(event.target.value)}>
                {PROVINCES.map((province) => (
                  <option key={province.code} value={province.code}>
                    {province.name}
                  </option>
                ))}
              </select>
            </div>
          </div>
        ) : null}

        <div className="rounded-2xl border border-default-200 bg-default-50 px-4 py-4">
          <p className="text-xs font-medium uppercase tracking-[0.16em] text-gray-500">선택된 시작점</p>
          <p className="mt-2 text-lg font-semibold">{submitValue.regionName}</p>
          <p className="mt-1 text-sm leading-6 text-gray-500">
            {selectionMode === 'NATIONAL'
              ? '전국 결과를 먼저 보고 시도와 지역 단위로 내려갑니다.'
              : '선택한 시도를 먼저 보여주고, 이후 지도에서 시군구 또는 선거구로 이어집니다.'}
          </p>
        </div>

        <div className="flex flex-col gap-3 pt-1 sm:flex-row">
          <Button
            type="button"
            color="default"
            className="font-medium"
            isLoading={isPending}
            onClick={() => onSubmit(submitValue)}>
            {selectionMode === 'NATIONAL' ? '전국에서 시작' : `${submitValue.regionName} 보기`}
          </Button>
          <Button type="button" variant="light" className="font-medium" onClick={onCancel}>
            닫기
          </Button>
        </div>
      </CardBody>
    </Card>
  );
}
