package com.everyones.lawmaking.common.dto;

import com.everyones.lawmaking.domain.entity.Party;
import com.everyones.lawmaking.domain.entity.RepresentativeProposer;
import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;

import java.util.List;

@Getter
@Builder
@AllArgsConstructor
@JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
public class PartyDto {
    private long partyId;
    private String partyName;
    private String partyImageUrl;

    public static PartyDto from(Party party) {
        return PartyDto.builder()
                .partyId(party.getId())
                .partyName(party.getName())
                .partyImageUrl(party.getPartyImageUrl())
                .build();
    }

    public static PartyDto from(RepresentativeProposer representativeProposer) {
        var party = representativeProposer.getCongressman().getParty();
        return PartyDto.from(party);
    }

}
