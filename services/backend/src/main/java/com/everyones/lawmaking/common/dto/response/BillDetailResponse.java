package com.everyones.lawmaking.common.dto.response;

import com.everyones.lawmaking.common.dto.*;
import com.everyones.lawmaking.common.dto.bill.BillDto;
import com.everyones.lawmaking.common.dto.proposer.RepresentativeProposerDto;
import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import jakarta.validation.constraints.NotNull;
import lombok.AllArgsConstructor;
import lombok.Getter;

import java.util.List;

@Getter
@AllArgsConstructor
@JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
public class BillDetailResponse extends BillDto {
    private List<SimilarBill> similarBills;
    private VoteResultResponse voteResultResponse;


    public BillDetailResponse(@NotNull BillInfoDto billInfoDto, @NotNull List<RepresentativeProposerDto> representativeProposerDto, @NotNull List<PublicProposerDto> publicProposerDtoList, @NotNull Boolean isBookMarked) {
        super(billInfoDto, representativeProposerDto, publicProposerDtoList, isBookMarked);
    }

    public void setSimilarBills(List<SimilarBill> similarBills) {
        this.similarBills = similarBills;
    }

    public void setVoteResultResponse(VoteResultResponse voteResultResponse) {
        this.voteResultResponse = voteResultResponse;
    }
}
