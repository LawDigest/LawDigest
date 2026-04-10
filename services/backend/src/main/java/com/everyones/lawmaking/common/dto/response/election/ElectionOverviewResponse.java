package com.everyones.lawmaking.common.dto.response.election;

import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import lombok.Builder;
import lombok.Getter;

@Getter
@Builder
@JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
public class ElectionOverviewResponse {

    private String selectedElectionId;
    private String uiTemplate; // "REGIONAL" or "CANDIDATE"
    private ElectionResultCardResponse defaultResultCard;

    @Getter
    @Builder
    @JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
    public static class ElectionResultCardResponse {
        private String sourceElectionId;
        private String regionType;
        private String regionCode;
        private String title;
    }
}
