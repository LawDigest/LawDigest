package com.everyones.lawmaking.common.dto;

import com.everyones.lawmaking.domain.entity.VoteParty;
import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;

@Getter
@Builder
@AllArgsConstructor
@JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
public class PartyVoteDto {
    private PartyDto partyInfo;
    private Integer partyApprovalCount;


    public static PartyVoteDto from(VoteParty voteParty) {
        return PartyVoteDto.builder()
                .partyInfo(PartyDto.from(voteParty.getParty()))
                .partyApprovalCount(voteParty.getVoteForCount())
                .build();
    }

}
