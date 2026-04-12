package com.everyones.lawmaking.common.dto.response.election.feed;

import com.everyones.lawmaking.domain.entity.poll.PollSurvey;
import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import lombok.Builder;
import lombok.Getter;

import java.time.LocalDate;

@Getter
@Builder
@JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
public class PollFeedPayload {

    private String registrationNumber;
    private String pollster;
    private String sponsor;
    private LocalDate surveyEndDate;
    private String region;
    private String electionName;
    private Integer sampleSize;
    private String marginOfError;
    private String sourceUrl;

    public static PollFeedPayload from(PollSurvey survey) {
        return PollFeedPayload.builder()
                .registrationNumber(survey.getRegistrationNumber())
                .pollster(survey.getPollster())
                .sponsor(survey.getSponsor())
                .surveyEndDate(survey.getSurveyEndDate())
                .region(survey.getRegion())
                .electionName(survey.getElectionName())
                .sampleSize(survey.getSampleSize())
                .marginOfError(survey.getMarginOfError())
                .sourceUrl(survey.getSourceUrl())
                .build();
    }
}
