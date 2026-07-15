import { Bill } from '@/components';
import { Divider } from '@heroui/react';
import { BillResponse } from '@/types';
import { getChairmanProposerInfo, isGovernmentBill } from '@/utils';
import { SectionContainer } from '../SectionContainer';
import { ProposerList } from '../ProposerList';
import { ProgressStage } from '../ProgressStage';
import { AnotherBillList } from '../AnotherBill';
import { ProcessResult } from '../ProcessResult';

export default function BillDetail({ data, viewCount }: { data: BillResponse; viewCount: number }) {
  const isGovernmentProposer = isGovernmentBill({
    proposerKind: data.bill_info_dto.proposer_kind,
    billId: data.bill_info_dto.bill_id,
    representativeProposerCount: data.representative_proposer_dto_list.length,
    publicProposerCount: data.public_proposer_dto_list.length,
  });
  const isChairmanProposer = Boolean(
    getChairmanProposerInfo({
      proposerKind: data.bill_info_dto.proposer_kind,
      proposerText: data.bill_info_dto.proposers,
      committee: data.bill_info_dto.committee,
    }),
  );

  return (
    <section>
      <Bill {...data} detail viewCount={viewCount}>
        <section className="md:w-[300px] lg:w-[490px] md:float-right flex flex-col gap-[34px] mt-[34px]">
          {!isGovernmentProposer && !isChairmanProposer && (
            <>
              <SectionContainer title="발의자 명단">
                <ProposerList
                  representativeProposerList={data.representative_proposer_dto_list}
                  publicProposerList={data.public_proposer_dto_list}
                  billId={data.bill_info_dto.bill_id}
                  proposerKind={data.bill_info_dto.proposer_kind}
                  proposeDate={data.bill_info_dto.propose_date}
                  popover={false}
                />
              </SectionContainer>

              <Divider className="hidden md:block h-[1px] w-full border-gray-1 dark:border-dark-l" />
            </>
          )}

          <SectionContainer title="심사 진행 단계">
            <ProgressStage billStage={data.bill_info_dto.bill_stage} />
          </SectionContainer>

          <Divider className="hidden md:block h-[1px] w-full border-gray-1 dark:border-dark-l" />

          <SectionContainer title="법안 처리 결과">
            <ProcessResult
              approval_count={data.vote_result_response.approval_count}
              total_vote_count={data.vote_result_response.total_vote_count}
              party_vote_list={data.vote_result_response.party_vote_list}
              bill_result={data.bill_info_dto.bill_result}
            />
          </SectionContainer>
        </section>
      </Bill>

      <div className="md:w-[calc(100%-340px)] lg:w-[calc(100%-530px)] border-r-[1px] md:dark:border-dark-l px-4 pt-[34px]">
        <SectionContainer>
          <AnotherBillList {...data} />
        </SectionContainer>
      </div>
    </section>
  );
}
