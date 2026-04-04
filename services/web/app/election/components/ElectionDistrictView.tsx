'use client';

import { useState } from 'react';
import { ConfirmedRegion } from './ElectionMapShell';
import { MOCK_DISTRICT, MockCandidate } from '../data/mockDistrictData';
import DistrictMapPicker from './shared/DistrictMapPicker';
import PollRegionPanel from './PollRegionPanel';
import FeedRegionPanel from './FeedRegionPanel';

interface ElectionDistrictViewProps {
  confirmedRegion: ConfirmedRegion | null;
  onRegionChange: (region: ConfirmedRegion) => void;
}

function CandidateCard({
  candidate,
  isSelected,
  onSelect,
}: {
  candidate: MockCandidate;
  isSelected: boolean;
  onSelect: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onSelect}
      className={[
        'flex flex-col items-center gap-2 p-4 rounded-2xl border transition-all min-w-[140px]',
        isSelected
          ? 'border-2 bg-default-50 dark:bg-dark-pb'
          : 'border-gray-1 dark:border-dark-l bg-white dark:bg-dark-pb',
      ].join(' ')}
      style={{ borderColor: isSelected ? candidate.partyColor : undefined }}>
      <div
        className="w-14 h-14 rounded-full flex items-center justify-center text-white font-bold text-xl"
        style={{ backgroundColor: candidate.partyColor }}>
        {candidate.name[0]}
      </div>
      <p className="text-sm font-semibold text-gray-4 dark:text-white">{candidate.name}</p>
      <p className="text-[11px] text-gray-2">{candidate.partyName}</p>
      <p className="text-[11px] text-gray-3 dark:text-gray-1 text-center leading-snug line-clamp-2">
        &ldquo;{candidate.slogan}&rdquo;
      </p>
      <span
        className="text-xs font-bold px-2 py-0.5 rounded-full text-white"
        style={{ backgroundColor: candidate.partyColor }}>
        {candidate.supportPct}%
      </span>
    </button>
  );
}

function CompareTable({ a, b }: { a: MockCandidate; b: MockCandidate }) {
  const rows = [
    { label: '정당', aVal: a.partyName, bVal: b.partyName },
    { label: '지지율', aVal: `${a.supportPct}%`, bVal: `${b.supportPct}%` },
    { label: '주요 공약', aVal: a.pledges[0], bVal: b.pledges[0] },
    { label: '경력', aVal: a.career[0], bVal: b.career[0] },
  ];
  return (
    <div className="mx-4 rounded-2xl border border-gray-1 dark:border-dark-l overflow-hidden">
      <div className="grid grid-cols-3 bg-default-50 dark:bg-dark-b text-[11px] font-semibold text-gray-3 dark:text-gray-1">
        <div className="p-3">항목</div>
        <div className="p-3 border-l border-gray-1 dark:border-dark-l">{a.name}</div>
        <div className="p-3 border-l border-gray-1 dark:border-dark-l">{b.name}</div>
      </div>
      {rows.map((row) => (
        <div key={row.label} className="grid grid-cols-3 border-t border-gray-1 dark:border-dark-l text-xs">
          <div className="p-3 text-gray-2 font-medium">{row.label}</div>
          <div className="p-3 border-l border-gray-1 dark:border-dark-l text-gray-4 dark:text-white">{row.aVal}</div>
          <div className="p-3 border-l border-gray-1 dark:border-dark-l text-gray-4 dark:text-white">{row.bVal}</div>
        </div>
      ))}
    </div>
  );
}

export default function ElectionDistrictView({ confirmedRegion, onRegionChange }: ElectionDistrictViewProps) {
  const [selectedCandidates, setSelectedCandidates] = useState<string[]>([]);
  const [showPicker, setShowPicker] = useState(false);

  function toggleCandidate(id: string) {
    setSelectedCandidates((prev) => {
      if (prev.includes(id)) return prev.filter((c) => c !== id);
      if (prev.length < 2) return [...prev, id];
      return [prev[1], id];
    });
  }

  const compareA = MOCK_DISTRICT.candidates.find((c) => c.id === selectedCandidates[0]);
  const compareB = MOCK_DISTRICT.candidates.find((c) => c.id === selectedCandidates[1]);

  if (!confirmedRegion || showPicker) {
    return (
      <div className="px-4 py-6 space-y-4">
        <div className="rounded-2xl border border-gray-1 dark:border-dark-l bg-white dark:bg-dark-pb p-5 space-y-4">
          <div className="text-center">
            <p className="text-base font-semibold text-gray-4 dark:text-white">내 지역구를 설정해보세요</p>
            <p className="text-sm text-gray-2 mt-1">지역구를 설정하면 후보자 비교와 여론조사를 볼 수 있어요.</p>
          </div>
          <DistrictMapPicker
            selected={null}
            onSelect={(region) => {
              if (region) {
                onRegionChange(region);
                setShowPicker(false);
              }
            }}
          />
          <p className="text-xs text-center text-gray-2">저장하려면 로그인이 필요합니다.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col pb-10">
      {/* 지역구 헤더 */}
      <div className="flex items-center gap-2 px-4 py-3 border-b border-gray-1 dark:border-dark-l">
        <span className="text-sm font-semibold text-gray-4 dark:text-white">📍 {confirmedRegion.regionName}</span>
        <button
          type="button"
          onClick={() => setShowPicker(true)}
          className="text-xs text-gray-2 hover:text-gray-3 dark:hover:text-gray-1 underline ml-auto">
          변경
        </button>
      </div>

      {/* 후보자 비교 섹션 */}
      <div className="py-4 space-y-4">
        <div className="flex items-center justify-between px-4">
          <h3 className="text-sm font-semibold text-gray-4 dark:text-white">후보자 비교</h3>
          {selectedCandidates.length > 0 && (
            <p className="text-[11px] text-gray-2">{selectedCandidates.length}/2명 선택됨</p>
          )}
        </div>
        <div className="flex gap-3 overflow-x-auto px-4 scrollbar-hide pb-2">
          {MOCK_DISTRICT.candidates.map((candidate) => (
            <CandidateCard
              key={candidate.id}
              candidate={candidate}
              isSelected={selectedCandidates.includes(candidate.id)}
              onSelect={() => toggleCandidate(candidate.id)}
            />
          ))}
        </div>
        {compareA && compareB && (
          <div className="pt-2">
            <CompareTable a={compareA} b={compareB} />
          </div>
        )}
        {selectedCandidates.length < 2 && (
          <p className="text-[11px] text-center text-gray-2 px-4">후보자 2명을 선택하면 비교표가 나타납니다.</p>
        )}
      </div>

      {/* 내 지역구 여론조사 */}
      <div className="border-t border-gray-1 dark:border-dark-l pt-4">
        <PollRegionPanel region={confirmedRegion.regionName} />
      </div>

      {/* 내 지역구 피드 */}
      <div className="border-t border-gray-1 dark:border-dark-l pt-4 mt-4">
        <FeedRegionPanel region={confirmedRegion.regionName} />
      </div>
    </div>
  );
}
