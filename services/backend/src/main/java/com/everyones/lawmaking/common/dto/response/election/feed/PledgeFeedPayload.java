package com.everyones.lawmaking.common.dto.response.election.feed;

import com.everyones.lawmaking.domain.entity.election.ElectionCandidate;
import com.everyones.lawmaking.domain.entity.election.ElectionPledge;
import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import lombok.Builder;
import lombok.Getter;

@Getter
@Builder
@JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
public class PledgeFeedPayload {

    private Long pledgeId;
    private String candidateName;
    private String partyName;
    private String region;
    private String prmsTitle;
    private String summary;

    public static PledgeFeedPayload from(ElectionPledge pledge) {
        ElectionCandidate candidate = pledge.getCandidate();
        return PledgeFeedPayload.builder()
                .pledgeId(pledge.getId())
                .candidateName(candidate != null ? candidate.getName() : null)
                .partyName(candidate != null ? candidate.getJdName() : null)
                .region(pledge.getNormalizedRegion())
                .prmsTitle(pledge.getPrmsTitle())
                .summary(pledge.getSummary())
                .build();
    }
}
