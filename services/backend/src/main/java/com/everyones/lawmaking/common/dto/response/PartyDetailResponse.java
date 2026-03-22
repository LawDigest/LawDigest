package com.everyones.lawmaking.common.dto.response;

import com.everyones.lawmaking.domain.entity.Party;
import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.persistence.Column;
import jakarta.validation.constraints.NotNull;
import lombok.*;

@AllArgsConstructor
@NoArgsConstructor
@Builder
@Data
@JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
public class PartyDetailResponse {

    @NotNull
    private long partyId;
    @NotNull
    private String partyName;
    @NotNull
    private String partyImgUrl;
    @NotNull
    private int proportionalCongressmanCount;
    @NotNull
    private int districtCongressmanCount;
    @NotNull
    private int totalCongressmanCount;
    @NotNull
    private int representativeBillCount;
    @NotNull
    private int publicBillCount;
    @NotNull
    private int followCount;
    @NotNull
    private boolean isFollowed;
    @NotNull
    private String websiteUrl;

    @Schema(name = "당대표")
    private String partyLeader;

    @Schema(name = "원내 대표")
    private String parliamentaryLeader;

    @Schema(name = "사무 총장")
    private String secretaryGeneral;

    @Schema(name = "정책위의장")
    private String policyCommitteeChairman;


    public static PartyDetailResponse from(Party party) {
        var partyFollow = party.getPartyFollow();
        return PartyDetailResponse.builder()
                .partyId(party.getId())
                .partyName(party.getName())
                .partyImgUrl(party.getPartyImageUrl())
                .websiteUrl(party.getWebsiteUrl())
                .proportionalCongressmanCount(party.getProportionalCongressmanCount())
                .districtCongressmanCount(party.getDistrictCongressmanCount())
                .totalCongressmanCount(0)
                .representativeBillCount(party.getRepresentativeBillCount())
                .publicBillCount(party.getPublicBillCount())
                .partyLeader(party.getPartyLeader())
                .parliamentaryLeader(party.getParliamentaryLeader())
                .secretaryGeneral(party.getSecretaryGeneral())
                .policyCommitteeChairman(party.getPolicyCommitteeChairman())
                .followCount(partyFollow.size())
                .isFollowed(false)
                .build();
    }

}
