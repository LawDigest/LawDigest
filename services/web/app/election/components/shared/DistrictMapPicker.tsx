'use client';

import { useCallback } from 'react';
import ManualRegionPicker, { ManualRegionFormValue } from '../ManualRegionPicker';

export interface SelectedRegion {
  regionCode: string;
  regionName: string;
}

interface DistrictMapPickerProps {
  selected: SelectedRegion | null;
  onSelect: (region: SelectedRegion | null) => void;
  label?: string;
}

function noop() {}

export default function DistrictMapPicker({ selected, onSelect, label = '지역 선택' }: DistrictMapPickerProps) {
  const handleSubmit = useCallback(
    (value: ManualRegionFormValue) => {
      onSelect({ regionCode: value.regionCode, regionName: value.regionName });
    },
    [onSelect],
  );

  const handleReset = useCallback(() => {
    onSelect(null);
  }, [onSelect]);

  if (selected) {
    return (
      <div className="flex items-center gap-2 px-4 py-2">
        <span className="inline-flex items-center gap-1.5 rounded-full bg-default-100 dark:bg-dark-pb px-3 py-1 text-sm font-medium text-gray-4 dark:text-white">
          <span aria-hidden="true">📍</span>
          <span>{selected.regionName}</span>
        </span>
        <button
          type="button"
          onClick={handleReset}
          className="text-xs text-gray-2 hover:text-gray-3 dark:hover:text-gray-1 underline">
          변경
        </button>
      </div>
    );
  }

  return (
    <div className="px-4 py-2">
      <p className="mb-2 text-sm text-gray-2 dark:text-gray-2">{label}</p>
      <ManualRegionPicker onSubmit={handleSubmit} onCancel={noop} />
    </div>
  );
}
