'use client';

import { Card, CardBody } from '@nextui-org/card';
import { Avatar } from '@nextui-org/avatar';
import { Chip } from '@nextui-org/chip';
import { ElectionId, ElectionCandidateSummary } from '@/types';

interface CandidateListProps {
  candidates: ElectionCandidateSummary[];
  selectedCandidateId: string | null;
  onSelect: (id: string) => void;
}

export default function CandidateList({
  candidates,
  selectedCandidateId,
  onSelect,
}: CandidateListProps) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 w-full p-4 md:p-6">
      {candidates.map((candidate) => (
        <Card
          key={candidate.candidate_id}
          isPressable
          onPress={() => onSelect(candidate.candidate_id)}
          className={`border dark:border-dark-l shadow-none hover:border-[#191919] transition-all ${
            selectedCandidateId === candidate.candidate_id ? 'ring-2 ring-[#191919] border-transparent' : ''
          }`}
        >
          <CardBody className="flex flex-col items-center gap-4 py-8 text-center">
            <Avatar
              src={candidate.candidate_image_url}
              className="w-24 h-24 text-large border-2 dark:border-dark-l"
              fallback={<span className="text-xl">{candidate.candidate_name[0]}</span>}
            />
            <div className="flex flex-col gap-2 items-center">
              <span className="font-bold text-lg">{candidate.candidate_name}</span>
              <Chip size="sm" variant="flat" color="primary">
                {candidate.party_name}
              </Chip>
            </div>
          </CardBody>
        </Card>
      ))}
      {!candidates.length && (
        <div className="col-span-full py-20 text-center text-gray-400">
          등록된 대선 후보자가 없습니다.
        </div>
      )}
    </div>
  );
}
