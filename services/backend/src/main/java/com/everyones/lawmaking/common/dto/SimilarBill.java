package com.everyones.lawmaking.common.dto;

import com.everyones.lawmaking.domain.entity.Bill;
import jakarta.validation.constraints.NotNull;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;

import java.util.ArrayList;
import java.util.List;

@Getter
@Builder
@AllArgsConstructor
public class SimilarBill {
    @NotNull
    private String billId;
    @NotNull
    private String billBriefSummary;
    @NotNull
    private String billName;
    @NotNull
    private String billProposers;
    private String billStage;
    @NotNull
    private List<PartyDto> party;

    public static SimilarBill from(Bill bill) {
        List<PartyDto> partyList = new ArrayList<>();
        var representProposers = bill.getRepresentativeProposer();
        for (var representProposer : representProposers) {
            partyList.add(PartyDto.from(representProposer.getCongressman().getParty()));
        }

        return SimilarBill.builder()
                .billId(bill.getId())
                .billBriefSummary(bill.getBriefSummary())
                .billName(bill.getBillName())
                .billProposers(bill.getProposers())
                .billStage(bill.getStage())
                .party(partyList)
                .build();
    }

}
