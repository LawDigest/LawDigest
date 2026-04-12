package com.everyones.lawmaking.common.dto.response.election.feed;

import com.everyones.lawmaking.domain.entity.Bill;
import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import lombok.Builder;
import lombok.Getter;

import java.time.LocalDate;

@Getter
@Builder
@JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
public class BillFeedPayload {

    private String billId;
    private String billName;
    private String proposers;
    private String committee;
    private LocalDate proposeDate;
    private String stage;
    private String summary;

    public static BillFeedPayload from(Bill bill) {
        return BillFeedPayload.builder()
                .billId(bill.getId())
                .billName(bill.getBillName())
                .proposers(bill.getProposers())
                .committee(bill.getCommittee())
                .proposeDate(bill.getProposeDate())
                .stage(bill.getStage())
                .summary(bill.getSummary())
                .build();
    }
}
