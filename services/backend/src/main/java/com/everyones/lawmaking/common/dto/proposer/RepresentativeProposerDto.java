package com.everyones.lawmaking.common.dto.proposer;

import com.everyones.lawmaking.domain.entity.Party;
import com.everyones.lawmaking.domain.entity.RepresentativeProposer;
import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import com.querydsl.core.annotations.QueryProjection;
import lombok.*;


@Builder
@Getter
@JsonNaming(value = PropertyNamingStrategies.SnakeCaseStrategy.class)
public class RepresentativeProposerDto {

    private String representativeProposerId;
    private String representativeProposerName;
    private String representProposerImgUrl;

    private long partyId;
    private String partyName;
    private String partyImageUrl;

    @QueryProjection
    public RepresentativeProposerDto(
            String representativeProposerId,
            String representativeProposerName,
            String representProposerImgUrl,
            long partyId,
            String partyName,
            String partyImageUrl) {
        this.representativeProposerId = representativeProposerId;
        this.representativeProposerName = representativeProposerName;
        this.representProposerImgUrl = representProposerImgUrl;
        this.partyId = partyId;
        this.partyName = partyName;
        this.partyImageUrl = partyImageUrl;

    }

    public static RepresentativeProposerDto from(RepresentativeProposer representativeProposer) {
        Party party = representativeProposer.getParty();
        return RepresentativeProposerDto.builder()
                .representativeProposerId(representativeProposer.getCongressman().getId())
                .representativeProposerName(representativeProposer.getCongressman().getName())
                .representProposerImgUrl(representativeProposer.getCongressman().getCongressmanImageUrl())
                .partyId(party.getId())
                .partyName(party.getName())
                .partyImageUrl(party.getPartyImageUrl())
                .build();
    }


}
