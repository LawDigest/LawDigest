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
public class ElectionPollCandidateResponse {

    private String selectedCandidate;
    private String basisQuestionKind;
    private List<String> candidateOptions;
    private List<CandidateTrendPoint> series;
    private List<CandidateSeries> comparisonSeries;
    private List<CandidateSnapshot> latestSnapshot;

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
    public static class CandidateTrendPoint {
        private SurveyReference survey;
        private BigDecimal percentage;
    }

    @Getter
    @Builder
    @JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
    public static class CandidateSeries {
        private String candidateName;
        private List<CandidateTrendPoint> series;
    }

    @Getter
    @Builder
    @JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
    public static class CandidateSnapshot {
        private String candidateName;
        private BigDecimal percentage;
    }
}
