package com.everyones.lawmaking.common.dto.response;

import com.everyones.lawmaking.domain.entity.Congressman;
import com.everyones.lawmaking.domain.entity.Party;
import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import jakarta.validation.constraints.NotNull;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;

@Getter
@AllArgsConstructor
@Builder
@JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
public class LikingCongressmanResponse {

    @NotNull
    private String congressmanId;

    @NotNull
    private String congressmanName;

    @NotNull
    private String congressmanImageUrl;

    @NotNull
    private Long partyId;

    @NotNull
    private String partyName;

    private String partyImageUrl;

    public static LikingCongressmanResponse from(Congressman congressman) {
        Party party = congressman.getParty();
        return LikingCongressmanResponse.builder()
                .congressmanId(congressman.getId())
                .congressmanName(congressman.getName())
                .congressmanImageUrl(congressman.getCongressmanImageUrl())
                .partyId(party.getId())
                .partyName(party.getName())
                .partyImageUrl(party.getPartyImageUrl())
                .build();
    }

}
