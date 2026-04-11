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
public class ElectionPollPartyResponse {

    private String selectedParty;
    private List<TrendPoint> trendSeries;
    private List<RegionalDistributionItem> regionalDistribution;

    @Getter
    @Builder
    @JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
    public static class TrendPoint {
        private SurveyReference survey;
        private BigDecimal percentage;
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
    public static class RegionalDistributionItem {
        private String regionName;
        private BigDecimal percentage;
    }
}
