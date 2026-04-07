'use client';

import PartyLogoReplacement from '@/components/common/PartyLogoReplacement/PartyLogoReplacement';

export interface Party {
  name: string;
  color: string;
}

interface PartyRingSelectorProps {
  parties: Party[];
  selected: string | null;
  onSelect: (partyName: string | null) => void;
}

export default function PartyRingSelector({ parties, selected, onSelect }: PartyRingSelectorProps) {
  return (
    <div className="flex gap-4 overflow-x-auto px-4 py-3 scrollbar-hide">
      {parties.map((party) => {
        const isSelected = selected === party.name;
        return (
          <button
            key={party.name}
            type="button"
            aria-pressed={isSelected}
            onClick={() => onSelect(isSelected ? null : party.name)}
            className="flex flex-col items-center gap-1.5 flex-shrink-0">
            <div
              className="rounded-full p-0.5 transition-all"
              style={{ boxShadow: isSelected ? `0 0 0 2.5px ${party.color}` : 'none' }}>
              <PartyLogoReplacement partyName={party.name} circle color={party.color} />
            </div>
            <span
              className={`text-[11px] max-w-[56px] text-center leading-tight transition-colors ${
                isSelected ? 'font-semibold text-gray-4 dark:text-white' : 'text-gray-2 dark:text-gray-2'
              }`}>
              {party.name}
            </span>
          </button>
        );
      })}
    </div>
  );
}
