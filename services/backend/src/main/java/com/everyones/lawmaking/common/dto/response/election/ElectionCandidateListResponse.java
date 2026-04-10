package com.everyones.lawmaking.common.dto.response.election;

import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import lombok.Builder;
import lombok.Getter;

import java.util.List;

@Getter
@Builder
@JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
public class ElectionCandidateListResponse {

    private String selectedElectionId;
    private String regionCode;
    private String officeType;
    private List<CandidateItem> candidates;

    @Getter
    @Builder
    @JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
    public static class CandidateItem {
        private Long candidateId;
        private String candidateName;
        private String partyName;
        private String candidateImageUrl;
        private String giho;
        private String status;
        private String candidateType;
    }
}
