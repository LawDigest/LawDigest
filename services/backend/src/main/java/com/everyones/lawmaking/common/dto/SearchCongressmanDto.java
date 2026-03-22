package com.everyones.lawmaking.common.dto;

import com.everyones.lawmaking.common.dto.response.SearchResponse;
import com.everyones.lawmaking.domain.entity.Congressman;
import com.everyones.lawmaking.global.constant.SearchType;
import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import jakarta.validation.constraints.NotNull;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;

@Builder
@Getter
@AllArgsConstructor
@JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
public class SearchCongressmanDto implements SearchResponse {
    @NotNull
    private String congressmanId;

    @NotNull
    private String congressmanName;

    @NotNull
    private String congressmanImageUrl;

    @NotNull
    private long partyId;

    @NotNull
    private String partyName;

    @NotNull
    private String searchType;


    public static SearchResponse from(Congressman congressman) {
        var party = congressman.getParty();
        return SearchCongressmanDto.builder()
                .congressmanId(congressman.getId())
                .congressmanName(congressman.getName())
                .congressmanImageUrl(congressman.getCongressmanImageUrl())
                .partyId(party.getId())
                .partyName(party.getName())
                .searchType(SearchType.CONGRESSMAN.name())
                .build();
    }
}
