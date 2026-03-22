package com.everyones.lawmaking.common.dto;

import com.everyones.lawmaking.domain.entity.VoteRecord;
import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

@Builder
@Data
@AllArgsConstructor
@NoArgsConstructor
@JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
public class VoteResultResponse {
    private Integer approvalCount;
    private Integer totalVoteCount;
    private List<PartyVoteDto> partyVoteList;

    public static VoteResultResponse of(VoteRecord voteRecord, List<PartyVoteDto> partyVoteList) {
        var voteResultBuilder = VoteResultResponse.builder()
                .partyVoteList(partyVoteList);
        if (voteRecord == null) {
            return voteResultBuilder.build();
        }

        return voteResultBuilder
                .approvalCount(voteRecord.getVoteForCount())
                .totalVoteCount(voteRecord.getTotalVoteCount())
                .build();
    }
}
