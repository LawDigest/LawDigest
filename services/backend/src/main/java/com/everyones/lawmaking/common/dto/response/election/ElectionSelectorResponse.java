package com.everyones.lawmaking.common.dto.response.election;

import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import lombok.Builder;
import lombok.Getter;

import java.util.List;

@Getter
@Builder
@JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
public class ElectionSelectorResponse {

    private String defaultElectionId;
    private List<ElectionItem> elections;

    @Getter
    @Builder
    @JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
    public static class ElectionItem {
        private String electionId;
        private String electionName;
        private String electionDate;
        private boolean upcoming;
    }
}
