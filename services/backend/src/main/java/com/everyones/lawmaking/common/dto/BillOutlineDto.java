package com.everyones.lawmaking.common.dto;

import com.everyones.lawmaking.domain.entity.Bill;
import com.everyones.lawmaking.domain.entity.RepresentativeProposer;
import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.util.ArrayList;
import java.util.List;

@Builder
@Getter
@AllArgsConstructor
@NoArgsConstructor
@JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
public class BillOutlineDto {
    private List<PartyDto> partyInfo;
    private String billId;
    private String billName;
    private String billStage;
    private String billResult;
    private String billProposers;
    private String billBriefSummary;


    public static BillOutlineDto from(Bill bill) {
        var representProposers = bill.getRepresentativeProposer();
        List<PartyDto> partyList = new ArrayList<>();
        for (RepresentativeProposer representativeProposer : representProposers) {
            var party = representativeProposer.getCongressman().getParty();
            partyList.add(PartyDto.from(party));
        }
        return BillOutlineDto.builder()
                .partyInfo(partyList)
                .billId(bill.getId())
                .billName(bill.getBillName())
                .billStage(bill.getStage())
                .billResult(bill.getBillResult())
                .billProposers(bill.getProposers())
                .billBriefSummary(bill.getBriefSummary())
                .build();
    }
}
