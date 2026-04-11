package com.everyones.lawmaking.common.dto.response.election;

import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import lombok.Builder;
import lombok.Getter;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;

@Getter
@Builder
@JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
public class ElectionPollRegionResponse {

    private String regionName;
    private List<PartySnapshot> partySnapshot;
    private List<CandidateSnapshot> candidateSnapshot;
    private List<SurveySummary> latestSurveys;

    @Getter
    @Builder
    @JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
    public static class PartySnapshot {
        private String partyName;
        private BigDecimal percentage;
    }

    @Getter
    @Builder
    @JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
    public static class CandidateSnapshot {
        private String candidateName;
        private BigDecimal percentage;
    }

    @Getter
    @Builder
    @JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
    public static class SurveySummary {
        private String registrationNumber;
        private String pollster;
        private LocalDate surveyEndDate;
    }
}
