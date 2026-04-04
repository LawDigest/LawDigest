'use client';

import { useState } from 'react';
import { ConfirmedRegion } from './ElectionMapShell';
import { MOCK_DISTRICT, MockCandidate, MockAiIssue, IMPORTANCE_LABEL } from '../data/mockDistrictData';
import DistrictMapPicker from './shared/DistrictMapPicker';
import PollRegionPanel from './PollRegionPanel';
import FeedRegionPanel from './FeedRegionPanel';

interface ElectionDistrictViewProps {
  confirmedRegion: ConfirmedRegion | null;
  onRegionChange: (region: ConfirmedRegion) => void;
}

// ─── 후보자 캐러셀 카드 ───────────────────────────────────────────────────────

function CandidateCard({
  candidate,
  isSelected,
  onSelect,
}: {
  candidate: MockCandidate;
  isSelected: boolean;
  onSelect: () => void;
}) {
  const importanceColor = isSelected ? candidate.partyColor : '#737c7f';

  return (
    <button
      type="button"
      onClick={onSelect}
      className="min-w-[272px] bg-white dark:bg-dark-pb rounded-2xl p-5 shadow-sm flex flex-col gap-4 text-left transition-all"
      style={{
        border: isSelected ? `2px solid ${candidate.partyColor}` : '1.5px solid #dbe4e7',
        outline: 'none',
      }}>
      {/* 헤더: 아바타 + 이름/정당 */}
      <div className="flex items-center gap-4">
        <div
          className="w-14 h-14 rounded-full flex items-center justify-center text-white font-bold text-xl shrink-0"
          style={{ backgroundColor: candidate.partyColor }}>
          {candidate.name[0]}
        </div>
        <div>
          <p className="text-[11px] font-bold uppercase tracking-widest" style={{ color: candidate.partyColor }}>
            {candidate.partyName}
          </p>
          <h4 className="font-bold text-base text-gray-4 dark:text-white mt-0.5">{candidate.name}</h4>
        </div>
        {/* 지지율 뱃지 */}
        <span
          className="ml-auto text-xs font-extrabold px-2.5 py-1 rounded-full text-white shrink-0"
          style={{ backgroundColor: candidate.partyColor }}>
          {candidate.supportPct}%
        </span>
      </div>

      {/* 주요 공약 목록 */}
      <div className="space-y-2">
        {candidate.pledges.slice(0, 2).map((pledge) => (
          <div key={pledge} className="flex items-start gap-2">
            <span
              className="material-symbols-outlined text-sm mt-0.5 shrink-0"
              style={{
                color: importanceColor,
                fontVariationSettings: "'FILL' 1",
              }}>
              star
            </span>
            <p className="text-xs text-gray-3 dark:text-gray-1 leading-relaxed">{pledge}</p>
          </div>
        ))}
      </div>
    </button>
  );
}

// ─── AI 주요 이슈 카드 ────────────────────────────────────────────────────────

function AiIssueItem({ issue }: { issue: MockAiIssue }) {
  const importanceColors: Record<MockAiIssue['importance'], string> = {
    high: 'text-secondary',
    medium: 'text-on-surface-variant',
    emerging: 'text-tertiary',
  };

  return (
    <div className="flex items-center gap-4 p-4 bg-white dark:bg-dark-pb rounded-2xl border border-gray-1 dark:border-dark-l">
      <div className="w-10 h-10 flex items-center justify-center rounded-xl bg-secondary/5 text-secondary shrink-0">
        <span className="material-symbols-outlined text-xl">{issue.icon}</span>
      </div>
      <div className="flex-1 min-w-0">
        <h4 className="font-bold text-sm text-gray-4 dark:text-white">{issue.title}</h4>
        <p className="text-xs text-gray-2 mt-0.5 leading-snug">{issue.description}</p>
      </div>
      <span className={`font-bold text-xs shrink-0 ${importanceColors[issue.importance]}`}>
        {IMPORTANCE_LABEL[issue.importance]}
      </span>
    </div>
  );
}

// ─── 지역구 여론 섹션 ─────────────────────────────────────────────────────────

function DistrictPollCard() {
  const { poll } = MOCK_DISTRICT;
  const otherPct = Math.max(0, 100 - poll.leadPct - poll.secondPct);

  return (
    <div className="bg-white dark:bg-dark-pb rounded-3xl p-6 border border-gray-1 dark:border-dark-l">
      {/* 상단: 1위/2위 수치 */}
      <div className="flex justify-between items-end mb-6">
        <div>
          <p className="text-2xl font-extrabold text-gray-4 dark:text-white">{poll.leadPct}%</p>
          <p className="text-xs font-bold uppercase tracking-wider mt-0.5" style={{ color: poll.leadPartyColor }}>
            {poll.leadParty}
          </p>
        </div>
        <div className="text-right">
          <p className="text-base font-bold" style={{ color: poll.secondPartyColor }}>
            {poll.secondPct}%
          </p>
          <p className="text-[10px] text-gray-2">{poll.secondParty}</p>
        </div>
      </div>

      {/* 바 차트 */}
      <div className="h-3 w-full flex rounded-full overflow-hidden mb-6">
        <div
          className="h-full transition-all"
          style={{ width: `${poll.leadPct}%`, backgroundColor: poll.leadPartyColor }}
        />
        <div
          className="h-full transition-all"
          style={{ width: `${poll.secondPct}%`, backgroundColor: poll.secondPartyColor }}
        />
        {otherPct > 0 && <div className="h-full flex-1 bg-gray-1 dark:bg-dark-l" />}
      </div>

      {/* 하단: 미결정/신뢰도 */}
      <div className="flex gap-3">
        <div className="flex-1 bg-default-50 dark:bg-dark-b rounded-xl p-3">
          <p className="text-[10px] font-bold text-gray-2 uppercase tracking-wide mb-1">미결정</p>
          <p className="text-lg font-extrabold text-gray-4 dark:text-white">{poll.undecidedPct}%</p>
        </div>
        <div className="flex-1 bg-default-50 dark:bg-dark-b rounded-xl p-3">
          <p className="text-[10px] font-bold text-gray-2 uppercase tracking-wide mb-1">신뢰도</p>
          <p className="text-lg font-extrabold text-gray-4 dark:text-white">{poll.reliability}%</p>
        </div>
      </div>
    </div>
  );
}

// ─── 지역 미설정 Empty State ──────────────────────────────────────────────────

function EmptyDistrictState({ onSelect }: { onSelect: (region: ConfirmedRegion) => void }) {
  const [showPicker, setShowPicker] = useState(false);

  if (showPicker) {
    return (
      <div className="px-4 py-6">
        <div className="rounded-2xl border border-gray-1 dark:border-dark-l bg-white dark:bg-dark-pb p-5 space-y-4">
          <div className="text-center">
            <p className="text-base font-semibold text-gray-4 dark:text-white">지역구를 선택해주세요</p>
            <p className="text-sm text-gray-2 mt-1">지역구를 설정하면 후보자 비교와 여론조사를 볼 수 있어요.</p>
          </div>
          <DistrictMapPicker
            selected={null}
            onSelect={(region) => {
              if (region) {
                onSelect(region);
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
    <div className="px-4 py-6">
      <div className="bg-default-50 dark:bg-dark-b border-2 border-dashed border-gray-1 dark:border-dark-l rounded-3xl p-8 text-center">
        <div className="w-16 h-16 bg-white dark:bg-dark-pb rounded-full flex items-center justify-center mx-auto mb-4 shadow-sm">
          <span className="material-symbols-outlined text-secondary text-3xl">location_off</span>
        </div>
        <h4 className="font-bold text-lg text-gray-4 dark:text-white mb-2">지역구를 설정해보세요</h4>
        <p className="text-sm text-gray-2 mb-6 leading-relaxed">
          GPS를 활성화하거나 지역구를 검색하면 후보자 정보와 지역 여론조사를 볼 수 있어요.
        </p>
        <button
          type="button"
          onClick={() => setShowPicker(true)}
          className="w-full py-4 rounded-full bg-secondary text-white font-bold text-sm transition-transform active:scale-95">
          지역구 검색
        </button>
      </div>
    </div>
  );
}

// ─── 메인 컴포넌트 ────────────────────────────────────────────────────────────

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

  if (!confirmedRegion || showPicker) {
    return (
      <EmptyDistrictState
        onSelect={(region) => {
          onRegionChange(region);
          setShowPicker(false);
        }}
      />
    );
  }

  const compareA = MOCK_DISTRICT.candidates.find((c) => c.id === selectedCandidates[0]);
  const compareB = MOCK_DISTRICT.candidates.find((c) => c.id === selectedCandidates[1]);

  return (
    <div className="flex flex-col pb-10">
      {/* ── 지역구 헤더 ── */}
      <section className="px-4 py-6 pb-4">
        <div className="flex items-end justify-between mb-2">
          <div>
            <span className="text-[11px] font-bold uppercase tracking-widest text-secondary opacity-70">내 지역구</span>
            <h2 className="font-bold text-2xl text-gray-4 dark:text-white mt-1">{confirmedRegion.regionName}</h2>
          </div>
          <button
            type="button"
            onClick={() => setShowPicker(true)}
            className="flex items-center justify-center w-10 h-10 rounded-full bg-default-50 dark:bg-dark-b text-secondary transition-colors hover:bg-gray-1">
            <span className="material-symbols-outlined text-xl">edit_location_alt</span>
          </button>
        </div>
        <div className="h-1 w-10 bg-secondary rounded-full" />
      </section>

      {/* ── 지역구 후보자 캐러셀 ── */}
      <section className="mb-8">
        <div className="flex items-center justify-between px-4 mb-3">
          <h3 className="font-bold text-base text-gray-4 dark:text-white">지역구 후보자</h3>
          <span className="text-xs text-gray-2">{MOCK_DISTRICT.candidates.length}명 출마</span>
        </div>
        <div className="flex gap-3 overflow-x-auto px-4 pb-3 scrollbar-hide">
          {MOCK_DISTRICT.candidates.map((candidate) => (
            <CandidateCard
              key={candidate.id}
              candidate={candidate}
              isSelected={selectedCandidates.includes(candidate.id)}
              onSelect={() => toggleCandidate(candidate.id)}
            />
          ))}
        </div>

        {/* 2명 선택 시 비교표 */}
        {compareA && compareB ? (
          <div className="mx-4 mt-3 rounded-2xl border border-gray-1 dark:border-dark-l overflow-hidden">
            <div className="grid grid-cols-3 bg-default-50 dark:bg-dark-b text-[11px] font-semibold text-gray-3 dark:text-gray-1">
              <div className="p-3">항목</div>
              <div className="p-3 border-l border-gray-1 dark:border-dark-l">{compareA.name}</div>
              <div className="p-3 border-l border-gray-1 dark:border-dark-l">{compareB.name}</div>
            </div>
            {[
              { label: '정당', aVal: compareA.partyName, bVal: compareB.partyName },
              { label: '지지율', aVal: `${compareA.supportPct}%`, bVal: `${compareB.supportPct}%` },
              { label: '주요 공약', aVal: compareA.pledges[0], bVal: compareB.pledges[0] },
              { label: '경력', aVal: compareA.career[0], bVal: compareB.career[0] },
            ].map((row) => (
              <div key={row.label} className="grid grid-cols-3 border-t border-gray-1 dark:border-dark-l text-xs">
                <div className="p-3 text-gray-2 font-medium">{row.label}</div>
                <div className="p-3 border-l border-gray-1 dark:border-dark-l text-gray-4 dark:text-white">
                  {row.aVal}
                </div>
                <div className="p-3 border-l border-gray-1 dark:border-dark-l text-gray-4 dark:text-white">
                  {row.bVal}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-[11px] text-center text-gray-2 px-4 mt-2">후보자 2명을 선택하면 비교표가 나타납니다.</p>
        )}
      </section>

      {/* ── AI 주요 이슈 ── */}
      <section className="px-4 mb-8">
        <div className="bg-default-50 dark:bg-dark-b rounded-3xl p-5 relative overflow-hidden">
          {/* 배경 장식 아이콘 */}
          <span
            className="material-symbols-outlined absolute top-3 right-4 text-5xl text-secondary opacity-10 select-none"
            aria-hidden>
            auto_awesome
          </span>

          <div className="flex items-center gap-2 mb-4">
            <span className="material-symbols-outlined text-secondary text-lg">auto_awesome</span>
            <h3 className="font-bold text-base text-gray-4 dark:text-white">
              AI 주요 이슈 · {confirmedRegion.regionName}
            </h3>
          </div>

          <div className="space-y-3">
            {MOCK_DISTRICT.aiIssues.map((issue) => (
              <AiIssueItem key={issue.id} issue={issue} />
            ))}
          </div>
        </div>
      </section>

      {/* ── 지역구 여론 ── */}
      <section className="px-4 mb-8">
        <h3 className="font-bold text-base text-gray-4 dark:text-white mb-3">지역구 여론</h3>
        <DistrictPollCard />
      </section>

      {/* ── 내 지역구 여론조사 (기존 패널) ── */}
      <section className="border-t border-gray-1 dark:border-dark-l pt-4">
        <PollRegionPanel region={confirmedRegion.regionName} />
      </section>

      {/* ── 내 지역구 피드 ── */}
      <section className="border-t border-gray-1 dark:border-dark-l pt-4 mt-4">
        <FeedRegionPanel region={confirmedRegion.regionName} />
      </section>
    </div>
  );
}
