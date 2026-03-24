'use client';

import { Card, CardBody, CardHeader, Spinner } from '@nextui-org/react';
import { ElectionCandidateId, ElectionId } from '@/types';
import { useGetElectionCandidateDetail } from '../apis/queries';

interface ElectionDetailPanelProps {
  electionId: ElectionId;
  candidateId: ElectionCandidateId | null;
  regionName?: string;
  fallbackCandidateName?: string;
  fallbackManifestoSummary?: string;
  fallbackManifestoItems?: string[];
}

interface ElectionDetailPanelContentProps {
  electionId: ElectionId;
  candidateId: ElectionCandidateId;
  regionName?: string;
  fallbackCandidateName?: string;
  fallbackManifestoSummary?: string;
  fallbackManifestoItems?: string[];
}

function ElectionDetailPanelContent({
  electionId,
  candidateId,
  regionName,
  fallbackCandidateName,
  fallbackManifestoSummary,
  fallbackManifestoItems,
}: ElectionDetailPanelContentProps) {
  const candidateDetailQuery = useGetElectionCandidateDetail(electionId, candidateId);
  const detail = candidateDetailQuery.data?.data;
  const manifestoItems = detail?.manifesto_items ?? fallbackManifestoItems ?? [];

  if (candidateDetailQuery.isLoading) {
    return (
      <Card className="h-fit border border-default-200 bg-transparent">
        <CardBody className="flex min-h-[280px] items-center justify-center">
          <Spinner color="default" label="후보 상세 정보를 불러오는 중입니다." />
        </CardBody>
      </Card>
    );
  }

  return (
    <Card className="h-fit border border-default-200 bg-transparent">
      <CardHeader className="flex flex-col items-start gap-2 p-6">
        <p className="text-sm font-medium text-gray-500">후보 상세</p>
        <div>
          <h3 className="text-2xl font-semibold">{detail?.candidate_name ?? fallbackCandidateName ?? '후보 정보'}</h3>
          <p className="mt-1 text-sm text-gray-500">{detail?.party_name ?? '정당 정보 없음'}</p>
          {regionName ? <p className="mt-2 text-xs text-gray-400">{regionName} 기준 문맥</p> : null}
        </div>
      </CardHeader>
      <CardBody className="space-y-5 p-6 pt-0">
        <section className="rounded-2xl border border-default-200 bg-default-50 p-4">
          <p className="text-xs font-medium uppercase tracking-[0.16em] text-gray-500">공약 요약</p>
          <p className="mt-3 text-sm leading-6">
            {detail?.manifesto_summary ?? fallbackManifestoSummary ?? '공약 요약 정보가 아직 없습니다.'}
          </p>
        </section>

        <section className="space-y-3">
          <p className="text-sm font-medium text-gray-500">세부 항목</p>
          {manifestoItems.length ? (
            <ul className="space-y-2">
              {manifestoItems.map((item) => (
                <li key={item} className="rounded-2xl border border-default-200 px-4 py-3 text-sm leading-6">
                  {item}
                </li>
              ))}
            </ul>
          ) : (
            <div className="rounded-2xl border border-dashed border-default-300 p-4 text-sm leading-6 text-gray-500">
              연결된 세부 공약 항목이 없습니다.
            </div>
          )}
        </section>
      </CardBody>
    </Card>
  );
}

export default function ElectionDetailPanel({
  electionId,
  candidateId,
  regionName,
  fallbackCandidateName,
  fallbackManifestoSummary,
  fallbackManifestoItems,
}: ElectionDetailPanelProps) {
  if (!candidateId) {
    return (
      <Card className="h-fit border border-default-200 bg-transparent">
        <CardBody className="flex min-h-[280px] items-center justify-center p-6 text-center text-sm leading-6 text-gray-500">
          후보를 선택하면 공약 요약과 세부 항목이 여기에 표시됩니다.
        </CardBody>
      </Card>
    );
  }

  return (
    <ElectionDetailPanelContent
      electionId={electionId}
      candidateId={candidateId}
      regionName={regionName}
      fallbackCandidateName={fallbackCandidateName}
      fallbackManifestoSummary={fallbackManifestoSummary}
      fallbackManifestoItems={fallbackManifestoItems}
    />
  );
}
