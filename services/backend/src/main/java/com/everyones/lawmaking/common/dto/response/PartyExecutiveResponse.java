package com.everyones.lawmaking.common.dto.response;

import com.everyones.lawmaking.domain.entity.Party;
import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;

@Getter
@AllArgsConstructor
@Builder
@JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
public class PartyExecutiveResponse {
    @Schema(description = "당대표", example = "이재명")
    String partyLeader;
    @Schema(description = "원내대표", example = "박찬대")
    String parliamentaryLeader;
    @Schema(description = "정책위의장", example = "진성준")
    String policyCommitteeChairman;
    @Schema(description = "사무총장", example = "박찬대")
    String secretaryGeneral;

    public static PartyExecutiveResponse from(Party party) {
        return PartyExecutiveResponse.builder()
                .partyLeader(party.getPartyLeader())
                .parliamentaryLeader(party.getParliamentaryLeader())
                .policyCommitteeChairman(party.getPolicyCommitteeChairman())
                .secretaryGeneral(party.getSecretaryGeneral())
                .build();
    }

}
