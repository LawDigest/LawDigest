'use client';

import { ElectionId, ElectionSelectorItem } from '@/types';
import { getElectionOptionDescription } from '../utils/electionLabels';

interface ElectionSelectorProps {
  elections: ElectionSelectorItem[];
  selectedElectionId: ElectionId;
  onChange: (electionId: ElectionId) => void;
}

export default function ElectionSelector({ elections, selectedElectionId, onChange }: ElectionSelectorProps) {
  return (
    <section className="grid gap-2">
      <div className="grid gap-2">
        <span className="text-sm font-medium text-gray-500">선거 선택</span>
        <select
          id="election-selector"
          aria-label="선거 선택"
          className="h-12 rounded-2xl border border-default-300 bg-transparent px-4 text-sm text-black outline-none transition focus:border-default-500"
          value={selectedElectionId}
          onChange={(event) => onChange(event.target.value)}>
          {elections.map((election) => (
            <option key={election.election_id} value={election.election_id}>
              {getElectionOptionDescription(election)}
            </option>
          ))}
        </select>
      </div>
    </section>
  );
}
