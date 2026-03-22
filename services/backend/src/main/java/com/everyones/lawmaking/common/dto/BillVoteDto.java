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
public class BillVoteDto {

    Integer voteCount;

    Long partyId;

    String partyName;

    String partyImageUrl;

    public static BillVoteDto from(VoteParty voteParty) {
        var party = voteParty.getParty();
        return BillVoteDto.builder()
                .voteCount(voteParty.getVoteForCount())
                .partyId(party.getId())
                .partyName(party.getName())
                .partyImageUrl(party.getPartyImageUrl())
                .build();
    }


}
