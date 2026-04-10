package com.everyones.lawmaking.common.dto.response.election;

import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import lombok.Builder;
import lombok.Getter;

import java.util.List;

@Getter
@Builder
@JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
public class ElectionRegionPanelResponse {

    private String selectedElectionId;
    private String regionCode;
    private String regionName;
    private Integer depth;
    private Integer totalCandidates;
    private List<OfficeTypeSummary> officeTypes;

    @Getter
    @Builder
    @JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
    public static class OfficeTypeSummary {
        private Integer sgTypecode;
        private String officeName;
        private Integer candidateCount;
    }
}
