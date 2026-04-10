package com.everyones.lawmaking.common.dto.response.election;

import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import lombok.Builder;
import lombok.Getter;

import java.util.List;

@Getter
@Builder
@JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
public class ElectionCandidateDetailResponse {

    private String selectedElectionId;
    private Long candidateId;
    private String candidateName;
    private String partyName;
    private String candidateImageUrl;
    private String gender;
    private Integer age;
    private String edu;
    private String job;
    private String career1;
    private String career2;
    private String sggName;
    private String sdName;
    private String giho;
    private String status;
    private String candidateType;
    private String manifestoSummary;
    private List<ManifestoItem> manifestoItems;

    @Getter
    @Builder
    @JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
    public static class ManifestoItem {
        private Integer order;
        private String title;
        private String content;
    }
}
