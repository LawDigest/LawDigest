package com.everyones.lawmaking.common.dto;

import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import com.querydsl.core.annotations.QueryProjection;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Getter
@NoArgsConstructor
@JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
public class CongressmanRankingDto {

    private String congressmanId;
    private String congressmanName;
    private String congressmanImageUrl;
    private long partyId;
    private String partyName;
    private String partyImageUrl;
    private long proposeCount;

    @QueryProjection
    public CongressmanRankingDto(
            String congressmanId,
            String congressmanName,
            String congressmanImageUrl,
            long partyId,
            String partyName,
            String partyImageUrl,
            Long proposeCount) {
        this.congressmanId = congressmanId;
        this.congressmanName = congressmanName;
        this.congressmanImageUrl = congressmanImageUrl;
        this.partyId = partyId;
        this.partyName = partyName;
        this.partyImageUrl = partyImageUrl;
        this.proposeCount = proposeCount == null ? 0L : proposeCount;
    }
}
