'use client';
import { ConfirmedRegion } from './ElectionMapShell';
export default function ElectionDistrictView(_: { confirmedRegion: ConfirmedRegion | null; onRegionChange: (r: ConfirmedRegion) => void }) {
  return <div className="p-8 text-center text-sm text-gray-2">내 지역구 탭 구현 중...</div>;
}
