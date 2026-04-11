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
public class ElectionPollOverviewResponse {

    private LeadingPartyResponse leadingParty;
    private List<PartyTrendPoint> partyTrend;
    private List<LatestSurveyResponse> latestSurveys;

    @Getter
    @Builder
    @JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
    public static class LeadingPartyResponse {
        private String partyName;
        private BigDecimal percentage;
        private String runnerUpParty;
        private BigDecimal gap;
        private BigDecimal undecided;
    }

    @Getter
    @Builder
    @JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
    public static class PartyTrendPoint {
        private SurveyReference survey;
        private List<PartySnapshot> snapshot;
    }

    @Getter
    @Builder
    @JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
    public static class SurveyReference {
        private String registrationNumber;
        private String pollster;
        private LocalDate surveyEndDate;
    }

    @Getter
    @Builder
    @JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
    public static class LatestSurveyResponse {
        private String registrationNumber;
        private String pollster;
        private LocalDate surveyEndDate;
        private List<PartySnapshot> snapshot;
    }

    @Getter
    @Builder
    @JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
    public static class PartySnapshot {
        private String partyName;
        private BigDecimal percentage;
    }
}
